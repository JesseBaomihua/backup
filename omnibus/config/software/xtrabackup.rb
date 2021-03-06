name "xtrabackup"
default_version "2.4.9"

skip_transitive_dependency_licensing true
dependency 'libffi'

source url: "https://s3.amazonaws.com/twindb-release/percona-xtrabackup-2.4.9.tar.gz",
       md5: "fca658cb3b004d2a2df342a136125f84"

relative_path "percona-xtrabackup-2.4.9"
whitelist_file /.*/

workers = 2

build do
    env = with_standard_compiler_flags(with_embedded_path)
    command "cmake -DBUILD_CONFIG=xtrabackup_release " \
          "-DWITH_MAN_PAGES=OFF -DDOWNLOAD_BOOST=1 " \
          "-DWITH_BOOST=#{install_dir}/libboost " \
          "-DWITH_SSL=system " \
          "-DINSTALL_BINDIR=#{install_dir}/embedded/bin", env: env

    make "-j #{workers}", env: env
    make "install", env: env
end
