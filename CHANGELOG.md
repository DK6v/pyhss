# Changelog

All notable changes to PyHSS are documented in this file, beginning from [Service Overhaul #168](https://github.com/nickvsnetworking/pyhss/pull/168).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2023-09-27

### Added

 - Systemd service files for PyHSS services
 - /oam/diameter_peers endpoint
 - /oam/deregister/{imsi} endpoint
 - /geored/peers endpoint
 - /geored/webhooks endpoint
 - Dependency on Redis for inter-service messaging
 - Significant performance improvements under load
 - Basic Rx support for RAA, AAA, ASA and STA
 - Rx MO call flow support (AAR -> RAR -> RAA -> AAA)
 - Dedicated bearer setup and teardown on Rx call
 - Asymmetric geored support
 - Configurable redis connection (Unix socket or TCP)
 - Basic database upgrade support in tools/databaseUpgrade
 - PCSCF state storage in ims_subscriber
 - (Experimental) Working horizontal scalability

### Changed

- Split logical functions of PyHSS into 6 service processes
- Logtool no longer handles metric processing
- Updated config.yaml
- Gx CCR-T now flushes PGW / IMS data, depending on Called-Station-Id
- Benchmarked lossless at ~100 diameter requests per second, per hssService.

### Fixed

 - Memory leaking in diameter.py
 - Gx CCA now supports apn inside a plmn based uri
 - AVP_Preemption_Capability and AVP_Preemption_Vulnerability now presents correctly in all diameter messages
 - Crash when webhook or geored endpoints enabled and no peers defined
 - CPU overutilization on all services

### Removed

- Multithreading in all services, except for metricService

[1.0.0]: https://github.com/nickvsnetworking/pyhss/releases/tag/v1.0.0