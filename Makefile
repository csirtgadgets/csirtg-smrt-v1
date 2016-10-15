NAME = csirtg-smrt
VERSION := $(shell git describe | cut -f1 -d' ')
OS = $(shell uname -s)
PYTHON = python

.PHONY: all build test

all: build test

test:
	py.test --cov=csirtg-smrt

pep8:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests"
	@echo "#############################################"
	-pep8 -r --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225,E261,E241 csirtg_smrt/

python:
	$(PYTHON) setup.py build

install:
	$(PYTHON) setup.py install

clean:
	@echo "Cleaning up distutils stuff"
	rm -rf build
	rm -rf dist
	@echo "Cleaning up byte compiled python stuff"
	find . -type f -regex ".*\.py[co]$$" -delete
	find . -type d -regex ".*__pycache__" -delete
	@echo "Cleaning up output from test runs"
	rm -rf tests/__pycache__
	@echo "Cleaning up RPM building stuff"
	rm -rf MANIFEST rpm-build
	@echo "Cleaning up Debian building stuff"
	find . -type f -name '*.pyc' -delete

sdist: clean
	$(PYTHON) setup.py sdist

wheel: clean
	$(PYTHON) setup.py bdist_wheel

# Pyinstaller params
# https://mborgerson.com/creating-an-executable-from-a-python-script
# TODO - move build up to main dir instead of cif/ fix the pathex in specs
PYINSTALLER = pyinstaller
PYINSTALLER_OPTS = --distpath=$(PYINSTALLER_DIST_PATH) --workpath=$(PYINSTALLER_WORK_PATH) -y --onefile
PYINSTALLER_SPEC_DIR = packaging/pyinstaller
PYINSTALLER_SPECS = csirtg-smrt.spec
PYINSTALLER_BUILD = pyinstaller-build
PYINSTALLER_DIST_PATH = dist
PYINSTALLER_WORK_PATH = temp
VERSION = `git describe`

bin:
	mkdir -p $(PYINSTALLER_BUILD) ;
	rm -rf $(PYINSTALLER_BUILD)/$(PYINSTALLER_WORK_PATH)/*
	cp -a csirtg_smrt $(PYINSTALLER_BUILD) ;
	echo $(VERSION) > _version ;
	cp -a $(PYINSTALLER_SPEC_DIR)/*.spec $(PYINSTALLER_BUILD)/ ;
	@for SPEC in $(PYINSTALLER_SPECS) ; do \
		(cd $(PYINSTALLER_BUILD) && $(PYINSTALLER) $(PYINSTALLER_OPTS) $${SPEC} ) ; \
	done

pyinstaller-clean:
	rm -rf


# DEB build parameters
DEBUILD_BIN ?= debuild
DPUT_BIN ?= dput
DPUT_OPTS ?=
DEB_DATE := $(shell date +"%a, %d %b %Y %T %z")
ifeq ($(OFFICIAL),yes)
    DEB_RELEASE = $(RELEASE)ppa
    # Sign OFFICIAL builds using 'DEBSIGN_KEYID'
    # DEBSIGN_KEYID is required when signing
    ifneq ($(DEBSIGN_KEYID),)
        DEBUILD_OPTS += -k$(DEBSIGN_KEYID)
    endif
else
    DEB_RELEASE = 0.git$(DATE)$(GITINFO)
    # Do not sign unofficial builds
    DEBUILD_OPTS += -uc -us
    DPUT_OPTS += -u
endif
DEBUILD = $(DEBUILD_BIN) $(DEBUILD_OPTS)
DEB_PPA ?= ppa
# Choose the desired Ubuntu release: lucid precise saucy trusty
DEB_DIST ?= stable

debian: pyinstaller-clean bin
	@for DIST in $(DEB_DIST) ; do \
	    mkdir -p deb-build/$${DIST}/$(NAME)-$(VERSION)/ ; \
	    cp -a packaging/debian deb-build/$${DIST}/$(NAME)-$(VERSION)/ ; \
	    cp -a $(PYINSTALLER_BUILD)/$(PYINSTALLER_DIST_PATH)/* deb-build/$${DIST}/$(NAME)-$(VERSION)/ ; \
        sed -ie "s|%VERSION%|$(VERSION)|g;s|%RELEASE%|$(DEB_RELEASE)|;s|%DIST%|$${DIST}|g;s|%DATE%|$(DEB_DATE)|g" deb-build/$${DIST}/$(NAME)-$(VERSION)/debian/changelog ; \
	done

deb: debian
	@for DIST in $(DEB_DIST) ; do \
	    (cd deb-build/$${DIST}/$(NAME)-$(VERSION)/ && $(DEBUILD) -b) ; \
	done
	@echo "#############################################"
	@echo "csirtg-smrt DEB artifacts:"
	@for DIST in $(DEB_DIST) ; do \
	    echo deb-build/$${DIST}/$(NAME)_$(VERSION)-$(DEB_RELEASE)~$${DIST}_amd64.changes ; \
	done
	@echo "#############################################"

debian-clean:
	rm -rf deb-build

# RPM build parameters
RPMSPECDIR= packaging/rpm
RPMSPEC = $(RPMSPECDIR)/bearded-avenger.spec
RPMDIST = $(shell rpm --eval '%{?dist}')
RPMRELEASE = $(RELEASE)
ifneq ($(OFFICIAL),yes)
    RPMRELEASE = 0.git$(DATE)$(GITINFO)
endif
RPMNVR = "$(NAME)-$(VERSION)-$(RPMRELEASE)$(RPMDIST)"

rpmcommon: pyinstaller-clean bin
	@mkdir -p rpm-build
	cp -a $(PYINSTALLER_DIST_PATH)/* rpm-build/
	cp -a packaging/rpm/*.spec rpm-build/
	@sed -e 's#^Version:.*#Version: $(VERSION)#' -e 's#^Release:.*#Release: $(RPMRELEASE)%{?dist}#' $(RPMSPEC) >rpm-build/$(NAME).spec

rpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	--define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm" \
	-ba rpm-build/$(NAME).spec
	@rm -f rpm-build/$(NAME).spec
	@echo "#############################################"
	@echo "bearded-avenger RPM is built:"
	@echo "    rpm-build/$(RPMNVR).noarch.rpm"
	@echo "#############################################"

clean: debian-clean pyinstaller-clean
