# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* Scaffolding for Task
* _Experiment_: Nightly heartbeat - runs a A-Z through the on premise CI on Discover every night
* _Task_: heartbeat
  * Run: writes down a `ci-metadata` file
  * Check: archives `ci-metadata` and checks it exists in the archive.
* _Task_: GEOS
  * Run: mepo clone GEOS, build a GEOS stack, export `GEOS_INSTALL` environement variable
  * Check: make sure `GEOS_INSTALL` is present
* _Task_: HeldSuarez
  * Run: copy inputs, wirte env setter and executor scripts, execute with srun
  * Check: barebone, check `ci-metadata` and archive logs
* _Task_: Physics standalones
  * Run: build a nvfortran OACC build of the physics standalone
  * Check: check computed values are 0.01% of the reference
* _Task_: CIClean
  * Run: clean the CI workspace from old working directory
* _Task_: SlurmCancelJob
  * Run: cancel all jobs of the username
* _Workflow_: "on demand" - triggered from the Action tab of github with configurable experiment and action
* _Workflow_: command on PR - triggered form a comment `/discover-ci experience-name experience-action`

### Changed

### Fixed

### Removed

### Deprecated
