# Getting Started
Parse data using [simple YAML](https://github.com/csirtgadgets/csirtg-smrt-py/wiki/Examples) and throw it just about anywhere.

```
$ [sudo] pip install csirtg-smrt
$ curl https://raw.githubusercontent.com/csirtgadgets/csirtg-smrt-py/master/examples/csirtg.yml > csirtg.yml
$ csirtg-smrt -r csirtg.yml -f port-scanners --format table|csv|bro

017-04-12 12:22:26,244 - INFO - csirtg_smrt.smrt[416] - loglevel is: INFO
2017-04-12 12:22:26,244 - INFO - csirtg_smrt.smrt[116] - processing csirtg.yml
2017-04-12 12:22:26,251 - INFO - csirtg_smrt.smrt[315] - processing: csirtg.yml - csirtg.io:port-scanners
+-------+----------+----------------------------+-----------------+-------+------------+---------+----------------------------------+-------+-----------+
|  tlp  |  group   |          lasttime          |    indicator    | count | confidence |   tags  |           description            | rdata | provider  |
+-------+----------+----------------------------+-----------------+-------+------------+---------+----------------------------------+-------+-----------+
| white | everyone | 2017-04-12T16:22:06.00000Z |   59.27.82.202  |   1   |    9.0     | scanner | sourced from firewall logs (in.. |       | csirtg.io |
| white | everyone | 2017-04-12T16:21:43.00000Z |  31.162.111.152 |   1   |    9.0     | scanner | sourced from firewall logs (in.. |       | csirtg.io |
| white | everyone | 2017-04-12T16:20:29.00000Z |    5.238.33.0   |   1   |    9.0     | scanner | sourced from firewall logs (in.. |       | csirtg.io |
...
```

[![YouTube](https://img.youtube.com/vi/0f6WLga2a6s/0.jpg)](https://www.youtube.com/watch?v=0f6WLga2a6s)

# Getting Involved
There are many ways to get involved with the project. If you have a new and exciting feature, or even a simple bugfix, simply [fork the repo](https://help.github.com/articles/fork-a-repo), create some simple test cases, [generate a pull-request](https://help.github.com/articles/using-pull-requests) and give yourself credit!

If you've never worked on a GitHub project, [this is a good piece](https://guides.github.com/activities/contributing-to-open-source) for getting started.

* [the Wiki](https://github.com/csirtgadgets/csirtg-smrt-py/wiki)  
* [Known Issues](https://github.com/csirtgadgets/csirtg-smrt-py/issues?labels=bug&state=open)  
* [How To Contribute](contributing.md)  
* [Mailing List](https://groups.google.com/forum/#!forum/ci-framework)  
* [Need Advanced Help?](https://csirtg.io/support) Partner with us!
 

# COPYRIGHT AND LICENCE

Copyright (C) 2018 [CSIRT Gadgets Foundation](http://csirtgadgets.org)

Free use of this software is granted under the terms of the Mozilla Public License (MPL2). For details see the file `LICENSE` included with the distribution.
