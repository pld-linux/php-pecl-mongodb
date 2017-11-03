# TODO
# - ix86/x32 (php -m) prints::
#   src/mongoc/mongoc-handshake.c:478 _append_and_truncate(): precondition failed: space_for_suffix >= 0
#   Aborted
#
# Conditional build:
%bcond_without	tests		# build without tests
%bcond_without	sasl		# Include Cyrus SASL support

%define		php_name	php%{?php_suffix}
%define		modname	mongodb
Summary:	MongoDB driver for PHP
Name:		%{php_name}-pecl-%{modname}
Version:	1.3.2
Release:	1
License:	Apache v2.0
Group:		Development/Languages/PHP
Source0:	https://pecl.php.net/get/%{modname}-%{version}.tgz
# Source0-md5:	6472d7fbfbbbd7e6efd0fc1011e4b7b5
Source1:	mongodb.ini
URL:		https://pecl.php.net/package/mongodb
BuildRequires:	%{php_name}-cli
BuildRequires:	%{php_name}-devel >= 4:5.4.0
BuildRequires:	%{php_name}-json
BuildRequires:	%{php_name}-pcre
BuildRequires:	%{php_name}-spl
%{?with_sasl:BuildRequires:	cyrus-sasl-devel}
BuildRequires:	libbson-devel >= 1.8.0
BuildRequires:	mongo-c-driver-devel >= 1.8.0
BuildRequires:	openssl-devel
BuildRequires:	rpmbuild(macros) >= 1.666
Requires:	%{php_name}-json
Requires:	%{php_name}-pcre
Requires:	%{php_name}-spl
%{?requires_php_extension}
Provides:	php(%{modname}) = %{version}
ExcludeArch:	%{ix86} x32
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
The purpose of this driver is to provide exceptionally thin glue
between MongoDB and PHP, implementing only fundemental and
performance-critical components necessary to build a fully-functional
MongoDB driver.

%prep
%setup -qc
mv %{modname}-%{version}/* .

# Ensure we use system library
# remove only C sources, m4 resources needed for phpize via m4_include
find \
	src/libbson \
	src/libmongoc \
	-name '*.[ch]' | xargs %{__rm} -v

%build
# Sanity check, really often broken
extver=$(sed -n '/#define PHP_MONGODB_VERSION/{s/.* "//;s/".*$//;p}' php_phongo.h)
if test "x${extver}" != "x%{version}"; then
	: Error: Upstream extension version is ${extver}, expecting %{version}.
	exit 1
fi

phpize

%configure \
	--with-libbson \
	--with-libmongoc \
	--with-mongodb-sasl=%{!?with_sasl:no}%{?with_sasl:yes} \
	--enable-mongodb

%{__make}

# simple module load test, always enabled
%{__php} -n -q \
	-d extension_dir=modules \
	-d extension=%{php_extensiondir}/pcre.so \
	-d extension=%{php_extensiondir}/spl.so \
	-d extension=%{php_extensiondir}/json.so \
	-d extension=%{modname}.so \
	-m > modules.log
grep %{modname} modules.log

%if %{with tests}
cat <<'EOF' > run-tests.sh
#!/bin/sh
export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 MALLOC_CHECK_=2
exec %{__make} test \
	PHP_EXECUTABLE=%{__php} \
	PHP_TEST_SHARED_SYSTEM_EXTENSIONS="pcre spl json" \
	RUN_TESTS_SETTINGS="-q $*"
EOF
chmod +x run-tests.sh

./run-tests.sh
%endif

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	EXTENSION_DIR=%{php_extensiondir} \
	INSTALL_ROOT=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d
cp -p %{SOURCE1} $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%config(noreplace) %verify(not md5 mtime size) %{php_sysconfdir}/conf.d/%{modname}.ini
%attr(755,root,root) %{php_extensiondir}/%{modname}.so
