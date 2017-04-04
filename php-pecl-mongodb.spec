#
# Conditional build:
%bcond_without	tests		# build without tests

%define		php_name	php%{?php_suffix}
%define		modname	mongodb
Summary:	MongoDB driver for PHP
Name:		php-pecl-%{modname}
Version:	1.2.8
Release:	0.1
License:	Apache v2.0
Group:		Development/Languages/PHP
Source0:	http://pecl.php.net/get/%{modname}-%{version}.tgz
# Source0-md5:	7c871c22fe7c8afdbe055e24075e95cf
URL:		https://pecl.php.net/package/mongodb
BuildRequires:	%{php_name}-devel
BuildRequires:	rpmbuild(macros) >= 1.666
%if %{with tests}
BuildRequires:	%{php_name}-json
%endif
BuildRequires:	cyrus-sasl-devel
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig(libbson-1.0) >= 1.5
BuildRequires:	pkgconfig(libmongoc-1.0) >= 1.5
Requires:	%{php_name}-json
%{?requires_php_extension}
Provides:	php(%{modname}) = %{version}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
The purpose of this driver is to provide exceptionally thin glue
between MongoDB and PHP, implementing only fundemental and
performance-critical components necessary to build a fully-functional
MongoDB driver.

%prep
%setup -qc
mv %{modname}-%{version}/* .

# Create configuration file
cat << 'EOF' > %{modname}.ini
; Enable %{summary} extension module
extension=%{modname}.so

; Configuration
;mongodb.debug=''
EOF

%build
# Sanity check, really often broken
extver=$(sed -n '/#define PHP_MONGODB_VERSION/{s/.* "//;s/".*$//;p}' php_phongo.h)
if test "x${extver}" != "x%{version}"; then
	: Error: Upstream extension version is ${extver}, expecting %{version}.
	exit 1
fi

phpize
# Ensure we use system library
# Need to be removed only after phpize because of m4_include
%{__rm} -r src/libbson
%{__rm} -r src/libmongoc

%configure \
	--with-libbson \
	--with-libmongoc \
	--enable-mongodb

%{__make}

%if %{with tests}
# simple module load test
%{__php} -n -q \
	-d extension_dir=modules \
	-d extension=%{php_extensiondir}/json.so \
	-d extension=%{modname}.so \
	-m > modules.log
grep %{modname} modules.log

export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 MALLOC_CHECK_=2
%{__make} test \
	PHP_EXECUTABLE=%{__php} \
	PHP_TEST_SHARED_SYSTEM_EXTENSIONS="json"
%endif

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	EXTENSION_DIR=%{php_extensiondir} \
	INSTALL_ROOT=$RPM_BUILD_ROOT

cp -p %{modname}.ini $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc LICENSE
%config(noreplace) %verify(not md5 mtime size) %{php_sysconfdir}/conf.d/%{modname}.ini
%attr(755,root,root) %{php_extensiondir}/%{modname}.so
