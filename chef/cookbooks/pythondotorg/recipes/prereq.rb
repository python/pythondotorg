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

package "libxslt-dev" do
  action :install
end

apt_repository "deadsnakes-python" do
  uri "http://ppa.launchpad.net/fkrull/deadsnakes/ubuntu precise main"
  keyserver "keyserver.ubuntu.com"
  key "DB82666C"
end

package "python3.3" do
  action :install
end
package "python3.3-dev" do
  action :install
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

bash "susy installation" do
  code "sudo gem install susy --version 1.0.rc.2"
  action :run
end
