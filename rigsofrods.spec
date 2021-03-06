# Fedora review: https://bugzilla.redhat.com/show_bug.cgi?id=rigsofrods

# %%global commit0 64ad6f6a2de8dc7e0ce3ee8c29cb8f0956197548
# %%global shortcommit0 %(c=%{commit0}; echo ${c:0:7})

Name:          rigsofrods
Version:       0.4.7.0
Release:       5%{?shortcommit0:.git.%{shortcommit0}}%{?dist}
Summary:       Vehicle simulator based on soft-body physics

# rigs-of-rods-0.4.7.0/source/main/utils/utf8/README.md *No copyright* CC by (v2.5)
License:       GPLv3 and CC-BY
URL:           http://www.rigsofrods.com/
Source0:       https://github.com/RigsOfRods/rigs-of-rods/archive/%{version}/%{name}-%{version}.tar.gz
# Recources http://www.rigsofrods.com/wiki/pages/Starting_RoR_under_Linux, unfortunately it is bu unknown licensing
# see https://github.com/RigsOfRods/rigs-of-rods/issues/542, so we can't redestribute them with package.
# Just provide autodownloader rc file for easy loading on first start
Source1:       rigsofrods-data-pack.autodownload_rc

BuildRequires: wxGTK-devel, ois-devel, ogre-devel >= 1.8.1, SocketW-devel, cmake
BuildRequires: ogre-pagedgeometry-devel, openal-devel, mygui-devel >= 3.2.0
BuildRequires: openssl-devel, dos2unix

# Caelum on review https://bugzilla.redhat.com/show_bug.cgi?id=879933 but it is recommendation only
# Disabled until https://github.com/RigsOfRods/rigs-of-rods/issues/550 resolved
# BuildRequires: caelum-devel

Requires:      unzip, autodownloader

# Update to 23c619a9010e375ea7357ef190ff683f2beac5d4 - https://github.com/RigsOfRods/rigs-of-rods/issues/534 closed. Build without angelscript until https://github.com/RigsOfRods/rigs-of-rods/issues/530 resolved.
# patch as sugested in https://github.com/RigsOfRods/rigs-of-rods/commit/23c619a9010e375ea7357ef190ff683f2beac5d4.
Patch1:        rigsofrods-0.4.6.0-without-angelscript.patch

%description
Rigs of Rods is an open source vehicle simulator licensed under the GNU General
Public License version 3. What makes Rigs of Rods different to most simulators
is its unique soft-body physics: vehicles, machines, objects, etc. are simulated
in real-time as flexible soft-body objects, giving the simulation an extremely
accurate behavior which entirely depends on the physical construction of the
vehicles or objects you create.
Features
- Soft-body physics. Objects according to their weight distribution,
    construction, and/or suspension (in the case of vehicles).
- Advanced flight model based on blade element theory. It allows the accurate
    simulation of any airplane, based entirely on its physical dimensions and
    wing airfoils, similar to X-Plane.
- Accurate buoyancy model based on elemental pressure gradients, enabling boats
    with complex hulls to move realistically in the swell.
- Basic support for dual-core processing. More multithreading and CUDA support
    is planned.
- Basic support for scripting using AngelScript.
- Based on the OGRE Graphics Engine.

%package data
Summary: Data files for %{name}
BuildArch: noarch

%description data
Data files for %{name} like images and maps.

%prep
%setup -qn rigs-of-rods-%{?commit0:%{commit0}}%{!?commit0:%{version}}
%patch1 -p1 -b .without-angelscript

# Convert lineendings
dos2unix --keepdate README.md COPYING

# Rpmlint
find . -type d -exec chmod 0755 {} \;

%build
cmake \
  -DROR_USE_MYGUI="TRUE" \
  -DROR_USE_OPENAL="TRUE" \
  -DROR_USE_PAGED="TRUE" \
  -DROR_USE_CAELUM="TRUE" \
  -DROR_USE_ANGELSCRIPT="FALSE" \
  -DROR_USE_SOCKETW="TRUE" \
  -DSOCKETW_INCLUDE_DIRS:PATH="%{_includedir}/SocketW" \
  -DPAGED_INCLUDE_DIRS:PATH="%{_includedir}/OGRE" \
  -MYGUI_INCLUDE_DIRS:PATH="%{_includedir}/OGRE/Overlay" \
  -DPAGED_LIBRARY_DIRS:PATH="%{_libdir}/OGRE" \
  -DPAGED_LIBRARIES=%{_libdir}/OGRE/libPagedGeometry.so \
  -DCAELUM_LIBRARIES=%{_libdir}/OGRE/libCaelum.so \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_INSTALL_PREFIX=%{buildroot}%{_prefix} \
  .

make %{?_smp_mflags}

%install
mkdir -p %{buildroot}/%{_libexecdir}/%{name} %{buildroot}/%{_bindir}
install -Dm 0755 bin/RoR %{buildroot}/%{_libexecdir}/%{name}/RoR
install -Dm 0755 bin/RoRConfig %{buildroot}/%{_libexecdir}/%{name}/RoRConfig
mkdir -p %{buildroot}/%{_datarootdir}/%{name}
# We will use skeleton.zip content
rm -rf bin/resources/skeleton
cp -pr bin/resources %{buildroot}/%{_datarootdir}/%{name}/
install -Dm 0644 %{SOURCE1} %{buildroot}/%{_datarootdir}/%{name}/

# base got from: tools/linux/binaries/plugins.cfg
cat <<EOF > %{buildroot}/%{_libexecdir}/%{name}/plugins.cfg
PluginFolder=%{_libdir}/OGRE/

Plugin=RenderSystem_GL
#Plugin=RenderSystem_GL3Plus
Plugin=Plugin_ParticleFX
Plugin=Plugin_OctreeSceneManager
#Plugin=Plugin_CgProgramManager
#Plugin=libCaelum.so
EOF

cat <<'EOF' > %{buildroot}/%{_bindir}/RoR
#!/bin/bash

echo "Please use RoRConfig to configure parameters of game"

if [ ! -e ~/.rigsofrods ]; then
  unzip %{_datarootdir}/%{name}/resources/skeleton.zip -d ~/.rigsofrods/
  # Can't ship with game: https://github.com/RigsOfRods/rigs-of-rods/issues/542
  %{_datarootdir}/autodl/AutoDL.py %{_datarootdir}/%{name}/rigsofrods-data-pack.autodownload_rc \
    && unzip ~/.rigsofrods/packs/pack_highquality04.zip -d ~/.rigsofrods/packs \
    && rm -f ~/.rigsofrods/packs/pack_highquality04.zip
  RoRConfig
fi

# cd required to read plugins.cfg in current directory! See https://github.com/RigsOfRods/rigs-of-rods/issues/541
cd %{_libexecdir}/%{name}
exec ./RoR "$@"
EOF

cat <<'EOF' > %{buildroot}/%{_bindir}/RoRConfig
#!/bin/bash

# cd required to read plugins.cfg in current directory! See https://github.com/RigsOfRods/rigs-of-rods/issues/541
cd %{_libexecdir}/%{name}
exec ./RoRConfig "$@"
EOF

%files
%doc AUTHORS.md BUILDING.md CONTRIBUTING.md DEPENDENCIES.md README.md
%license COPYING
%attr(0755,-,-) %{_bindir}/RoR
%attr(0755,-,-) %{_bindir}/RoRConfig
%dir %{_libexecdir}/%{name}
%{_libexecdir}/%{name}/RoR
%{_libexecdir}/%{name}/RoRConfig
%{_libexecdir}/%{name}/plugins.cfg

%files data
%{_datarootdir}/%{name}

%changelog
* Thu Nov 02 2017 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.7.0-5
- Move cmake run into %%build stage

* Thu Nov 02 2017 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.7.0-4
- Drop CXXFLAGS adjusting because in fresh versions system boost used by default (https://github.com/RigsOfRods/rigs-of-rods/commit/17ab75843545407433dc319e1aaa6831eb854b87)

* Tue Oct 31 2017 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.7.0-3
- Separate licenses by "and"
- Move CXXFLAGS specification into build stage

* Sun Oct 15 2017 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.7.0-2
- Review starts by Robert-André Mauchin. Thank you. Changes by notes.
- Simplified source URL.
- Move COPYING ro %%license from %%doc
- Add CC-BY into license tag
- Split-off -data sub-package (/usr/share)

* Tue Jan 31 2017 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.7.0-1
- Upstream now use github: https://github.com/RigsOfRods/rigs-of-rods
- Update to 0.4.7.0 release.
- Failed issue fail on GCC 7.0 - https://github.com/Hubbitus/rpm-rigsofrods/issues/1

* Sat Aug 06 2016 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.6.0-0.7.git.64ad6f6
- Update to 64ad6f6.
- Update high quality pack URL (by https://github.com/RigsOfRods/rigs-of-rods/issues/602#issuecomment-224537716)

* Sun Jan 24 2016 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.6.0-0.6.git.3e56c07
- Issue with compilation on ARM resolved (https://github.com/RigsOfRods/rigs-of-rods/issues/608).
- Drop rigsofrods-0.4.6.0-mygui-gt-2.2.1.patch as it incorporated (https://github.com/RigsOfRods/rigs-of-rods/issues/156 -> https://github.com/RigsOfRods/rigs-of-rods/pull/547)

* Sun Jan 17 2016 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.6.0-0.5.git.23c619a
- Does not compiled on ARM - https://github.com/RigsOfRods/rigs-of-rods/issues/608. Excluded.

* Sat Jan 16 2016 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.6.0-0.4.git.23c619a
- Report segfault: https://github.com/RigsOfRods/rigs-of-rods/issues/550 - temporary disable caelum (it is optional dep).
- Add BR openssl-devel
- Report new segfault: https://github.com/RigsOfRods/rigs-of-rods/issues/602
- Hit issue https://github.com/RigsOfRods/rigs-of-rods/issues/156. Add patch igsofrods-0.4.6.0-mygui-gt-2.2.1.patch.

* Sun Jan 10 2016 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.6.0-0.3.git.23c619a
- Update to 23c619a9010e375ea7357ef190ff683f2beac5d4 - https://github.com/RigsOfRods/rigs-of-rods/issues/534 closed. Build without angelscript until https://github.com/RigsOfRods/rigs-of-rods/issues/530 resolved.
- Add patch rigsofrods-0.4.6.0-without-angelscript.patch for 534 issue as sugested in https://github.com/RigsOfRods/rigs-of-rods/commit/23c619a9010e375ea7357ef190ff683f2beac5d4.

* Fri Jan 08 2016 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.6.0-0.2.git.c10f9ac
- Use autodownloader to easy download high quality pack (can't be redistributed https://github.com/RigsOfRods/rigs-of-rods/issues/542)

* Wed Jan 06 2016 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.6.0-0.1.git.c10f9ac
- Update to upstream release 0.4.6.0 (https://github.com/RigsOfRods/rigs-of-rods/issues/145#issuecomment-169460584).
- Project now on github.
- Fill https://github.com/RigsOfRods/rigs-of-rods/issues/530 about outdated AngelScript API usage. Disable AngelScript for now.
- Step to unreliased versions (due to the https://github.com/RigsOfRods/rigs-of-rods/issues/145)
- Fill https://github.com/RigsOfRods/rigs-of-rods/issues/534 (ScriptEngine.h: No such file or directory) - add temporary patch1: rigsofrods-0.4.6.0-build-without-angelscript.patch
- Upstream informed about incorrect fsf address: https://github.com/RigsOfRods/rigs-of-rods/issues/538
- Fill https://github.com/RigsOfRods/rigs-of-rods/issues/541 about required /usr/bin//plugins.cfg

* Sun Jan 27 2013 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.0.4-3
- Try link with angelscript 2.25.2 with patch by Dan Horák (https://bugzilla.redhat.com/show_bug.cgi?id=879931#c3)
- According to changelog make changes ( http://redmine.rigsofrods.com/issues/956 )
    Add Patch3: rigsofrods-0.4.0.4-angelscript-gt-2.22.patch
- BR caelum-devel instead of caelum.
- Add explicit linking to boost_system (https://svn.boost.org/trac/boost/ticket/7241, https://github.com/hobbes1069/Field3D/commit/544cca15426dfaa55b4e43843ea0bbd5c9569178)

* Sun Nov 25 2012 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.0.4-2
- Fix RoRconfig file.
- Add resources.

* Sat Sep 22 2012 Pavel Alexeev <Pahan@Hubbitus.info> - 0.4.0.4-1
- New version.
- Remade paths libs patch: rigsofrods-0.4.0.4-paths-libs.patch
- Add patches 2 and 3.

* Sun Jun 24 2012 Pavel Alexeev <Pahan@Hubbitus.info> - 0.39.4-1
- Initial spec version.
1