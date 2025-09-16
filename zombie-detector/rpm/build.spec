Name:           zombie-detector
Summary:        A FastAPI application for detecting zombie machines in a network.
License:        MIT
URL:            https://repo1.naudit.es/santander-cantabria/zombie-detector


%description
Zombie Detector is a FastAPI application for detecting zombie machines in a network
based on performance criteria including CPU, RAM, and network traffic patterns.
It provides both CLI and REST API interfaces for zombie host detection.

%global __requires_exclude ^python3dist\\(kafka-python\\).*
# We bundle it for RHEL configurations
Provides: bundled(python3dist(kafka-python)) = 2.0.2
BuildRequires: python3dist(pip) >= 19
BuildRequires: python3dist(wheel)


%install
# Create required directories
mkdir -p %{buildroot}%{_localstatedir}/log/zombie-detector
mkdir -p %{buildroot}%{_localstatedir}/lib/zombie-detector
mkdir -p %{buildroot}%{_sysconfdir}/zombie-detector
mkdir -p %{buildroot}%{_datadir}/zombie-detector

# Install vendored kafka-python from SOURCES/vendor-wheels
%{__python3} -m pip install \
  --no-deps --no-index \
  --find-links %{_sourcedir}/vendor-wheels \
  --root %{buildroot} --prefix %{_prefix} \
  kafka_python


# Install config files
install -D -m 644 zombie_detector/config/zombie-detector.ini %{buildroot}%{_sysconfdir}/zombie-detector/zombie-detector.ini
install -D -m 644 zombie_detector/config/states.json %{buildroot}%{_sysconfdir}/zombie-detector/states.json

#Install initial tracking files
install -D -m 644 zombie_detector/config/initial_tracking_files/current_zombies.json %{buildroot}%{_localstatedir}/lib/zombie-detector/current_zombies.json
install -D -m 644 zombie_detector/config/initial_tracking_files/zombie_history.json %{buildroot}%{_localstatedir}/lib/zombie-detector/zombie_history.json
install -D -m 644 zombie_detector/config/initial_tracking_files/killed_zombies.json %{buildroot}%{_localstatedir}/lib/zombie-detector/killed_zombies.json

# Install the systemd service
install -D -m 644 packaging/systemd/zombie-detector.service %{buildroot}%{_unitdir}/zombie-detector.service
# Install environment file
install -D -m 644 packaging/systemd/zombie-detector.default %{buildroot}%{_sysconfdir}/default/zombie-detector

%pre
# Create system user and group
getent group zombie-detector >/dev/null || groupadd -r zombie-detector
getent passwd zombie-detector >/dev/null || \
    useradd -r -g zombie-detector -d /var/lib/zombie-detector -s /sbin/nologin \
    -c "Zombie Detector service account" zombie-detector
exit 0

%post
chown -R zombie-detector:zombie-detector /var/log/zombie-detector
chown -R zombie-detector:zombie-detector /var/lib/zombie-detector
chown -R zombie-detector:zombie-detector /etc/zombie-detector
# Set proper permissions for tracking files
chmod 644 /var/lib/zombie-detector/*.json

# Initialize tracking files if they don't exist (safety check)
if [ ! -f /var/lib/zombie-detector/current_zombies.json ]; then
    echo '{"timestamp": null, "zombies": [], "zombie_ids": [], "stats": {"total_zombies": 0, "new_zombies": 0, "persisting_zombies": 0, "killed_zombies": 0}}' > /var/lib/zombie-detector/current_zombies.json
    chown zombie-detector:zombie-detector /var/lib/zombie-detector/current_zombies.json
fi

if [ ! -f /var/lib/zombie-detector/zombie_history.json ]; then
    echo '{"history": []}' > /var/lib/zombie-detector/zombie_history.json
    chown zombie-detector:zombie-detector /var/lib/zombie-detector/zombie_history.json
fi

if [ ! -f /var/lib/zombie-detector/killed_zombies.json ]; then
    echo '{"killed_zombies": []}' > /var/lib/zombie-detector/killed_zombies.json
    chown zombie-detector:zombie-detector /var/lib/zombie-detector/killed_zombies.json
fi


%systemd_post zombie-detector.service

%preun
%systemd_preun zombie-detector.service

%postun
%systemd_postun_with_restart zombie-detector.service

%files
%doc README.md
%dir %{_sysconfdir}/zombie-detector
%dir %{_localstatedir}/log/zombie-detector
%dir %{_localstatedir}/lib/zombie-detector
%config(noreplace) %{_sysconfdir}/zombie-detector/zombie-detector.ini
%config(noreplace) %{_sysconfdir}/zombie-detector/states.json
%config(noreplace) %{_localstatedir}/lib/zombie-detector/current_zombies.json
%config(noreplace) %{_localstatedir}/lib/zombie-detector/zombie_history.json
%config(noreplace) %{_localstatedir}/lib/zombie-detector/killed_zombies.json
%{_unitdir}/zombie-detector.service
%{_sysconfdir}/default/zombie-detector