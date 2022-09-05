Release v0.0.1 (2022-09-02)
---------------------------

Publish this version for testing release CI.
Change logs are written for demonstration purposes only.

### Features

* Add a command line tool to run the program.
* [follower](https://boholder.github.io/puntgun/configuration/plan-configuration#follower) - filter user by follower count.

### Improvements

* Add more logs for Client class.

### Removals

* Remove optional fields on `block` user action rule.

### Bug Fixes

* Fix rxpy(reactivex) repeat querying client to unnecessarily consuming additional API resource.

### Documentation

* Update CONTRIBUTING.md, add bold format on tools and CI concern.

### Dependencies

* [pydantic](https://pydantic-docs.helpmanual.io/) `1.9.2` -> `1.9.3`

### Miscellany

* Add [bug report](https://github.com/boholder/puntgun/blob/main/.github/ISSUE_TEMPLATE/bug_report.md) issue template.