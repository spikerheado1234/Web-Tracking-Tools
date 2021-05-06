import daemon
import track

config_json = track.load_config()

with daemon.DaemonContext(chroot_directory=None, working_directory=config_json['working_dir']):
    track.main()
