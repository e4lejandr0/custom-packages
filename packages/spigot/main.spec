# Don't put rpm package in subdir see: https://stackoverflow.com/questions/2565509/rpmbuild-generates-rpm-in-which-subdirectory
%define _build_name_fmt %{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}.rpm
# Drop the RPM in PWD
%define _rpmdir %{getenv:PWD}
%define _srcrpmdir %{getenv:PWD}
# spigot does not provide a checksum, we're trusting TLS
%define _disable_source_fetch %{nil}
%define _sourcedir %{getenv:PWD}
Name: spigot
Version: 1.15.2
Release: 0%{?dist}
Summary: High performance minecraft server

License: GPL v3
URL:     https://getbukkit.org
Source0: https://cdn.getbukkit.org/%{name}/%{name}-%{version}.jar
Source1: main.service.j2
Source2: firewalld.xml.j2

BuildRequires: ansible
Requires: java-11-openjdk
BuildArch: noarch

%define spigot_datadir %{_sharedstatedir}/%{name}
%define systemd_unitdir %{_prefix}/lib/systemd/system
%define firewalld_servicesdir %{_prefix}/lib/firewalld/services

%description
An implementation of the Bukkit plugin API for Minecraft servers, currently maintained by SpigotMC.

%prep
# no prep needed

%build
# binary release

%install
install -D -m=644 %{SOURCE0} %{buildroot}%{spigot_datadir}/%{name}.jar
mkdir -p %{buildroot}%{systemd_unitdir}
mkdir -p %{buildroot}%{firewalld_servicesdir}
ansible -m template \
    -a 'src=%{SOURCE1} dest=%{buildroot}%{systemd_unitdir}/%{name}.service' \
    -e '{
        "spigot_dir": "%{spigot_datadir}",
        "rpm_name": "%{name}"
    }' \
    localhost

ansible -m template \
    -a 'src=%{SOURCE2} dest=%{buildroot}%{firewalld_servicesdir}/%{name}.xml' \
    -e '{
         "rpm_name": "%{name}",
         "rpm_description": "%{name} server",
         "spigot_ports": [25565]
    }' \
    localhost

%clean
rm %{SOURCE0}
rm -rf %{buildroot}

%pre
if ! getent passwd %{name} 2>/dev/null >&2; then
   useradd --home-dir %{spigot_datadir} --shell /sbin/nologin --system %{name}
fi

%post
systemctl daemon-reload
systemctl reload firewalld


%files
%attr(755, %{name}, %{name}) %{spigot_datadir}
%attr(644, root, root) %{systemd_unitdir}/%{name}.service
%attr(644, root, root) %{firewalld_servicesdir}/%{name}.xml

%changelog
