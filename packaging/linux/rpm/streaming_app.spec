Name:           streaming-app
Version:        1.0.0
Release:        1%{?dist}
Summary:        Cross-Platform Legal Streaming App

License:        MIT and CC-BY-3.0
URL:            https://github.com/streaming-app/platform
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  gcc-c++, cmake, gtk3-devel, mpv-devel
Requires:       gtk3, mpv-libs

%description
High-performance legal streaming platform for Linux desktop environments
supporting hardware accelerated HLS and MP4 playback.

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/bin
mkdir -p $RPM_BUILD_ROOT/usr/share/applications
cp streaming_app $RPM_BUILD_ROOT/usr/bin/
ln -sf streaming_app $RPM_BUILD_ROOT/usr/bin/streaming-app
cp streaming_app.desktop $RPM_BUILD_ROOT/usr/share/applications/

%files
/usr/bin/streaming_app
/usr/bin/streaming-app
/usr/share/applications/streaming_app.desktop

%changelog
* Sat Sep 19 2026 Antigravity Engineering <eng@streaming-app.local> - 1.0.0-1
- Initial Phase 5 Linux desktop release
