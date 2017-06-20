# tjioi-printing

Print service for TJ IOI.

The reason this exists is because the contest VM (tjioi.vm.sites.tjhsst.edu) only has an IPv6 address, so it can't access any IPv4 services. On the other hand, the Syslab CUPS server (cups2.csl.tjhsst.edu) is only reachable through IPv4. Therein lies the problem.

This was set up as a service on my personal webdocs (on user.tjhsst.edu) and reverse-proxied with nginx to appear on the same domain as the contest site. Yes, it was kind of hacky. Next year, the setup may have to be appreciably different to account for various changes.
