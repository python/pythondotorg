# Install python and virtualenv

package "python-virtualenv" do
  action :install
end

package "libsqlite3-dev" do
  action :install
end

package "sqlite3" do
  action :install
end

package "bzip2" do
  action :install
end

package "libbz2-dev" do
  action :install
end

package "subversion" do
  action :install
end

remote_file "#{Chef::Config[:file_cache_path]}/Python-3.3.0.tar.bz2" do
  source "http://python.org/ftp/python/3.3.0/Python-3.3.0.tar.bz2"
  mode "0644"
  not_if { ::File.exists?("/usr/local/bin/python3.3") }
  notifies :run, "execute[install-python33]", :immediately
end

execute "install-python33" do
    cwd Chef::Config[:file_cache_path]
    command <<-EOF
    tar jxf Python-3.3.0.tar.bz2
    cd Python-3.3.0
    ./configure
    make &&  make install
    EOF
    action :nothing
end

# support libraries for PIL
package "libpng-dev" do
  action :install
end
package "libjpeg-dev" do
  action :install
end
package "libz-dev" do
  action :install
end

# Compass is used to compile sass files dynamically at deployment
gem_package 'compass' do
  version '0.11.7'
  action :install
end

gem_package 'susy' do
  version '1.0.rc.2'  # This is current the pre-release version
  action :install
end