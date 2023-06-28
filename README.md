<!--
Copyright © 2023 Intel Corporation

SPDX-License-Identifier: MIT
-->

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sigopt/sigopt-config/main.svg)](https://results.pre-commit.ci/latest/github/sigopt/sigopt-config/main)
![pre-commit](https://github.com/sigopt/sigopt-config/actions/workflows/pre-commit.yml/badge.svg)
![security](https://github.com/sigopt/sigopt-config/actions/workflows/documentation.yml/badge.svg)
![tests](https://github.com/sigopt/sigopt-config/actions/workflows/integration.yml/badge.svg)

# Sigopt-Config

Sigopt-Config is an open-source tool for managing configuration for SigOpt deployments from [sigopt-server](https://github.com/sigopt/sigopt-server).

## Usage

Configuration files must be stored in a single directory with a flat structure (no sub-directories). Each configuration file must contain a top-level mapping. Currently only JSON and YAML are supported.

The configuration directory is loaded into a native object (`object` in Javascript and `dict` in Python) via the following algorithm:

1.  A list of the files in the specified directory is created.
2.  The list of files is sorted by ascending lexographical order of filename.
3.  The files are read and parsed as YAML into a list of data.
4.  The list of data is reduced in reverse order via [JSON Merge Patch](https://datatracker.ietf.org/doc/html/rfc7386) with the empty object as the initializer.
5.  The result of the reduction is the final configuration object.

This algorithm has the following desirable properties:

- Individual configuration files can be reused across multiple environments
- Configuration files can be organized according to their purpose
- File precedence can be set by using appropriate filename prefixes
- Nested objects are merged together predictably
- Simple to implement consistenly in multiple languages provided the language has a YAML parser and JSON Merge Patch implementation
