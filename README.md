# TUF Demo for Docker Distributed Systems Summit #

## Table of Contents ##
- [How to Create and Modify a TUF Repository](#how-to-create-and-modify-a-tuf-repository)
  - [Overview](#overview)
  - [Keys](#keys)
    - [Create RSA Keys](#create-rsa-keys)
    - [Import RSA Keys](#import-rsa-keys)
    - [Create and Import Ed25519 Keys](#create-and-import-ed25519-keys)
  - [Create Top-level Metadata](#create-top-level-metadata)
    - [Create Root](#create-root)
    - [Create Timestamp, Snapshot, Targets](#create-timestamp-snapshot-targets)
  - [Targets](#targets)
    - [Add Target Files](#add-target-files)
  - [Delegations](#delegations)
  - [Wrap-up](#wrap-up)
- [How to Perform an Update](#how-to-perform-an-update)
- [Blocking Malicious Update](#blocking-malicious-update)
  - [Arbitrary Package Attack](#arbitrary-package-attack) 

## How to Create and Modify a TUF Repository ##


### Overview ###
A software update system must follow two steps to integrate The Update
Framework (TUF).  First, it must add the framework to the client side of the
update system.  The [tuf.client.updater](client/README.md) module assists in
integrating TUF on the client side.  Second, the repository on the server side
must be modified to include a minimum of four top-level metadata (root.json,
targets.json, snapshot.json, timestamp.json).  No additional software is
required to convert a repository to a TUF one.  The repository tool that
generates the required TUF metadata is the focus of this demo.  In addition,
the update procedure of a TUF integration is demonstrated and some malicious
updates are attempted.

The [repository tool](repository_tool.py) contains functions to generate all of
the files needed to populate and manage a TUF repository.  The tool may either
be imported into a Python module or used with the Python interpreter in
interactive mode.  For instance, here is an example of loading a TUF repository
in interactive mode:

```Bash
$ python
Python 2.7.3 (default, Sep 26 2013, 20:08:41) 
[GCC 4.6.3] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> from tuf.repository_tool import *
>>> repository = load_repository("/path/to/repository")
```

A repository object that encapsulates the metadata files of the repository can
be created or loaded by the repository tool.  Repository maintainers modify the
repository object to update metadata files stored on the repository.  TUF uses
the metadata files to validate files requested and downloaded by clients.  In
addition to the repository object, where the majority of changes are made, the
repository tool provides functions to generate and persist cryptographic keys.
The framework utilizes cryptographic keys to sign and verify metadata files.

To begin the demo, cryptographic keys are generated.  Before metadata files can
be validated by clients and target files fetched in a secure manner, public
keys must be pinned to particular metadata roles and signatures generated by
the private keys.  After covering keys, the four required top-level roles are
created next.  Examples are given demonstrating the expected work flow, where
the metadata roles are created in a specific order, keys imported and loaded,
and the metadata objects signed and written to disk.  Lastly, target files are
added to the repository, included in metadata, and a custom delegation
performed to extend the default roles of the repository.  By the end, a fully
populated TUF repository is generated that can be used to securely download
updates.

### Keys ###
The repository tool supports multiple public-key algorithms, such as
[RSA](https://en.wikipedia.org/wiki/RSA_%28cryptosystem%29) and
[Ed25519](http://ed25519.cr.yp.to/), and multiple cryptography libraries
(PyCrypto, pyca/cryptography, and PyNaCl).

To start, a public and private RSA key pair is generated with the
`generate_and_write_rsa_keypair()` function.  The keys generated will sign the
repository metadata files created in upcoming sub-sections.


#### Create RSA Keys ####
```python
>>> from tuf.repository_tool import *

# Generate and write the first of two root keys for the TUF repository.  The
# following function creates an RSA key pair, where the private key is saved to
# "keystore/root_key" and the public key to "keystore/root_key.pub".
# The 'keystore' directory can be manually created in the current directory
# to store the keys that we create in these examples.
>>> generate_and_write_rsa_keypair("keystore/root_key", bits=2048, password="password")

# If the key length is unspecified, it defaults to 3072 bits. A length of less 
# than 2048 bits raises an exception. A password may be supplied as an 
# argument, otherwise a user prompt is presented.
>>> generate_and_write_rsa_keypair("keystore/root_key2")
Enter a password for the RSA key:
Confirm:
```
The following four key files should now exist:

1.  **root_key**
2.  **root_key.pub**
3.  **root_key2**
4.  **root_key2.pub**

### Import RSA Keys ###
```python
>>> from tuf.repository_tool import *

# Import an existing public key.
>>> public_root_key = import_rsa_publickey_from_file("keystore/root_key.pub")

# Import an existing private key.  Importing a private key requires a password, whereas
# importing a public key does not.
>>> private_root_key = import_rsa_privatekey_from_file("keystore/root_key")
Enter a password for the encrypted RSA key:
```
`import_rsa_privatekey_from_file()` raises a `tuf.CryptoError` exception if the
key / password is invalid.

### Create and Import Ed25519 Keys ###
```Python
>>> from tuf.repository_tool import *

# Generate and write an ed25519 key pair.  The private key is saved encrypted.
# A 'password' argument may be supplied, otherwise a prompt is presented.
>>> generate_and_write_ed25519_keypair('keystore/ed25519_key')
Enter a password for the ED25519 key: 
Confirm:

# Import the ed25519 public key just created . . .
>>> public_ed25519_key = import_ed25519_publickey_from_file('keystore/ed25519_key.pub')

# and its corresponding private key.
>>> private_ed25519_key = import_ed25519_privatekey_from_file('keystore/ed25519_key')
Enter a password for the encrypted ED25519 key: 
```

### Create Top-level Metadata ###
The [metadata document](../METADATA.md) outlines the JSON metadata files that
must exist on a TUF repository.  The following sub-sections provide the
`repository_tool.py` calls repository maintainers may issue to generate the
required roles.  The top-level roles to be created are `root`, `timestamp`,
`snapshot`, and `target`.

We begin with `root`, the root of trust that specifies the public keys of the 
top-level roles, including itself. 


#### Create Root ####
```python
# Continuing from the previous section . . .

# Create a new Repository object that holds the file path to the repository and
# the four top-level role objects (Root, Targets, Snapshot, Timestamp).
# Metadata files are created when repository.write() is called.  The repository
# directory is created if it does not exist.  You may see log messages
# indicating any directories created.
>>> repository = create_new_repository("repository/")

# The Repository instance, 'repository', initially contains top-level Metadata
# objects.  Add one of the public keys, created in the previous section, to the
# root role.  Metadata is considered valid if it is signed by the public key's
# corresponding private key.
>>> repository.root.add_verification_key(public_root_key)

# Role keys (i.e., the key's keyid) may be queried.  Other attributes include:
# signing_keys, version, signatures, expiration, threshold, delegations
# (Targets role), and compressions.
>>> repository.root.keys
['b23514431a53676595922e955c2d547293da4a7917e3ca243a175e72bbf718df']

# Add a second public key to the root role.  Although previously generated and
# saved to a file, the second public key must be imported before it can added
# to a role.
>>> public_root_key2 = import_rsa_publickey_from_file("keystore/root_key2.pub")
>>> repository.root.add_verification_key(public_root_key2)

# Threshold of each role defaults to 1.   Maintainers may change the threshold
# value, but repository_tool.py validates thresholds and warns users.  Set the
# threshold of the root role to 2, which means the root metadata file is
# considered valid if it contains at least two valid signatures.  We also
# load the second private key, which hasn't been imported yet.
>>> repository.root.threshold = 2
>>> private_root_key2 = import_rsa_privatekey_from_file("keystore/root_key2", password="password")

# Load the root signing keys to the repository, which writeall() or write()
# (write multiple roles, or a single role, to disk) uses to sign the root
# metadata.  The load_signing_key() method SHOULD warn when the key is NOT
# explicitly allowed to sign for it.

>>> repository.root.load_signing_key(private_root_key)
>>> repository.root.load_signing_key(private_root_key2)

# Print the roles that are "dirty" (i.e., that have not been written to disk
# or have changed.
>>> repository.dirty_roles()
Dirty roles: ['root']

# The status() function also prints the next role(s) that needs editing.
# In this example, the 'targets' role needs editing next, since the root
# role is now fully valid.
>>> repository.status()
'targets' role contains 0 / 1 public keys.

# In the next section, update the other top-level roles and create a repository
# with valid metadata.
```

#### Create Timestamp, Snapshot, Targets
Now that `root.json` has been set, the other top-level roles may be created.
The signing keys added to these roles must correspond to the public keys
specified by the root.  

On the client side, `root.json` must always exist.  The other top-level roles,
created next, are requested by repository clients in (Timestamp -> Snapshot ->
Root -> Targets) order to ensure required metadata is downloaded in a secure
manner.

```python
# Continuing from the previous section . . .
>>> import datetime

# Generate keys for the remaining top-level roles.  The root keys have been set above.
# The password argument may be omitted if a password prompt is needed. 
>>> generate_and_write_rsa_keypair("keystore/targets_key", password="password")
>>> generate_and_write_rsa_keypair("keystore/snapshot_key", password="password")
>>> generate_and_write_rsa_keypair("keystore/timestamp_key", password="password")

# Add the public keys of the remaining top-level roles.
>>> repository.targets.add_verification_key(import_rsa_publickey_from_file("keystore/targets_key.pub"))
>>> repository.snapshot.add_verification_key(import_rsa_publickey_from_file("keystore/snapshot_key.pub"))
>>> repository.timestamp.add_verification_key(import_rsa_publickey_from_file("keystore/timestamp_key.pub"))

# Import the signing keys of the remaining top-level roles.  Prompt for passwords.
>>> private_targets_key = import_rsa_privatekey_from_file("kestore/targets_key")
Enter a password for the encrypted RSA key:

>>> private_snapshot_key = import_rsa_privatekey_from_file("keystore/snapshot_key")
Enter a password for the encrypted RSA key:

>>> private_timestamp_key = import_rsa_privatekey_from_file("keystore/timestamp_key")
Enter a password for the encrypted RSA key:

# Load the signing keys of the remaining roles so that valid signatures are
# generated when repository.writeall() is called.
>>> repository.targets.load_signing_key(private_targets_key)
>>> repository.snapshot.load_signing_key(private_snapshot_key)
>>> repository.timestamp.load_signing_key(private_timestamp_key)

# Write all metadata to "repository/metadata.staged/".  The common case is to crawl the
# filesystem for all delegated roles in "metadata.staged/".
>>> repository.writeall()
```

### Targets ###
TUF verifies target files by including their length, hash(es),
and filepath in metadata.  The filepaths are relative to a `targets/` directory
on the repository.  A TUF client can download a target file by first updating 
the latest copy of metadata (and thus available targets), verifying that their
length and hashes are valid, and then saving them locally to complete the update
process.

In this section, the target files intended for clients are added to a repository
and listed in `targets.json` metadata.

#### Add Target Files ####

The repository maintainer adds target files to roles (e.g., `targets`,
`unclaimed`) by specifying target paths.  Files at these target paths
must exist before the repository tool can generate and add their (hash(es),
length, filepath) to metadata.

The actual target files are added first to the `targets/` directory of the
repository.

```Bash
# Create and save target files to the targets directory of the repository.
$ cd repository/targets/
$ echo 'file1' > file1.txt
$ echo 'file2' > file2.txt
$ echo 'file3' > file3.txt
$ mkdir myproject; echo 'file4' > myproject/file4.txt
```

With the target files available on the `targets/` directory of the repository,
the `add_targets()` method of a Targets role can be called to add the target
files to metadata.

```python
>>> from tuf.repository_tool import *
>>> import os

# Load the repository created in the previous section.  This repository so far
# contains metadata for the top-level roles, but no target paths are yet listed
# in targets metadata.
>>> repository = load_repository("repository/")

# get_filepaths_in_directory() returns a list of file paths in a directory.  It can also return
# files in sub-directories if 'recursive_walk' is True.
>>> list_of_targets = repository.get_filepaths_in_directory("repository/targets/",
                                                        recursive_walk=False, followlinks=True) 

# Add the list of target paths to the metadata of the top-level Targets role.
# Any target file paths that might already exist are NOT replaced.
# add_targets() does not create or move target files on the file system.  Any
# target paths added to a role must be relative to the targets directory,
# otherwise an exception is raised.
>>> repository.targets.add_targets(list_of_targets)
```

The private keys of roles affected by the changes above must now be imported and
loaded.  `targets.json` must be signed because a target file was added to its
metadata.  `snapshot.json` keys must be loaded and its metadata signed because
`targets.json` has changed.  Similarly, since `snapshot.json` has changed, the
`timestamp.json` role must also be signed.

```Python
# The private key of the updated targets metadata must be loaded before it can
# be signed and written (Note the load_repository() call above).
>>> private_targets_key = import_rsa_privatekey_from_file("keystore/targets_key")
Enter a password for the encrypted RSA key:

>>> repository.targets.load_signing_key(private_targets_key)

# Due to the load_repository() and new versions of metadata, we must also load
# the private keys of Snapshot and Timestamp to generate a valid set of metadata.
>>> private_snapshot_key = import_rsa_privatekey_from_file("keystore/snapshot_key")
Enter a password for the encrypted RSA key:
>>> repository.snapshot.load_signing_key(private_snapshot_key)

>>> private_timestamp_key = import_rsa_privatekey_from_file("keystore/timestamp_key")
Enter a password for the encrypted RSA key:
>>> repository.timestamp.load_signing_key(private_timestamp_key)

# Which roles are dirty?
>>> repository.dirty_roles()
Dirty roles: ['timestamp', 'snapshot', 'targets']

# Generate new versions of the modified top-level metadata (targets, snapshot,
# and timestamp).
>>> repository.writeall()
```

### Delegations ###
All of the target files available on the repository created so far have been
added to one role.  But, what if multiple developers are responsible for the
files of a project?  What if responsiblity separation is desired?  Performing a
delegation, where one parent role delegates trust of some paths to another
role, is an option for integrators that require custom roles in addition to the
top-level roles available by default.

In the next sub-section, a delegated `unclaimed` role is delegated from the
top-level `targets` role.  The `targets` role specifies the delegated role's
public keys, the paths it is trusted to provide, and its role name.
Futhermore, the example below demonstrates a nested delegation from `unclaimed`
to `django`.  Once a parent role has delegated trust, delegated roles may add
targets and generate signed metadata.


```python
# Continuing from the previous section . . .

# Generate a key for a new delegated role named "django".
>>> generate_and_write_rsa_keypair("keystore/django_key", bits=2048, password="password")
>>> public_django_key = import_rsa_publickey_from_file("keystore/django_key.pub")

# Make a delegation from "targets" to "django", initially containing zero
# targets.
# delegate(rolename, list_of_public_keys, list_of_file_paths, threshold,
#          restricted_paths, path_hash_prefixes)
>>> repository.targets.delegate("django", [public_django_key], [])

# Load the private key of "django" so that signatures are later added and
# valid metadata is created.
>>> private_django_key = import_rsa_privatekey_from_file("keystore/django_key")
Enter a password for the encrypted RSA key:

>>> repository.targets("django").load_signing_key(private_django_key)

# Update an attribute of the unclaimed role.
>>> repository.targets("django").version = 2

# Dirty roles?
$ repository.dirty_roles()
Dirty roles: ['timestamp', 'snapshot', 'targets', 'django']

#  Write the metadata of "django", "root", "targets", "snapshot,
# and "timestamp".
>>> repository.writeall()
```

#### Wrap-up ####

In summary, the five steps a repository maintainer follows to create a basic TUF
repository are:

1.  Generate a repository directory that contains TUF metadata and the target files.
2.  Create top-level roles (`root.json`, `snapshot.json`, `targets.json`, and `timestamp.json`.) 
3.  Add target files to the `targets` role.
4.  Optionally, create delegated roles to distribute target files.
5.  Write the changes.

The repository tool saves repository changes to a `metadata.staged` directory.
Repository maintainers may push final changes to the "live" repository by
copying the staged directory to its destination. 
```Bash
# Copy the staged metadata directory changes to the live repository.
$ cp -r "repository/metadata.staged/" "repository/metadata/"
```

## How to Perform an Update ##

Documentation for setting up a TUF client and performing an update is
provided [here](client_setup_and_repository_example.md).

The following [repository tool](README.md) function creates a directory
structure that a client downloading new software using TUF (via
tuf/client/updater.py) expects. The `root.json` metadata file must exist, and
also the directories that hold the metadata files downloaded from a repository.
Software updaters integrating with TUF may use this directory to store TUF
updates saved on the client side.

```python
>>> from tuf.repository_tool import *
>>> create_tuf_client_directory("repository/", "client/")
```

`create_tuf_client_directory()` moves metadata from `repository/metadata` to
`client/` in this example.  The repository in `repository/` may be the
repository example created in the repository tool [README](README.md).


## Test TUF Locally ##
Run the local TUF repository server.
```Bash
$ cd "repository/"; python -m SimpleHTTPServer 8001
```

Retrieve targets from the TUF repository and save them to `client/`.  The
`basic_client.py` script is available in the 'scripts' directory.  In the
following example, it is copied to the 'client' directory and executed from
there.  In a different command-line prompt . . .
```Bash
$ cd "client/"
$ ls
metadata/

# Copy tuf/scripts/basic_client.py to current directory. 
$ python basic_client.py --repo http://localhost:8001
$ ls . targets/
.:
metadata  targets  tuf.log

targets/:
file1.txt  file2.txt file3.txt
```

## Blocking Malicious Updates ##
TUF protects against a number of attacks, some of which include replay,
arbitrary packages, mix and match attacks, etc.  In the next section
we show how the client is expected to reject a target file downloaded
from the repository that doesn't match what is listed in metadata.

### Arbitrary Package Attack ###
```Bash
$ mv 'repository/targets/file3.txt' 'repository/targets/file3.txt.backup'
$ echo 'bad_target' > 'repository/targets/file3.txt'
```

We next reset our local timestamp (so that a new update is prompted), and 
the target files previously downloaded.
rm -rf 'repository/targets/" 'client/metadata/current/timestamp.json"

Now we can perform an update that should detect the invalid target file...
```Bash
$ python basic_client.py --repo http://localhost:8001
Error: No working mirror was found:
  localhost:8001: BadHashError()
```
