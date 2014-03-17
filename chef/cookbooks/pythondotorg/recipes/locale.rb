# set locale to en_US.UTF-8 (which matches the live server) everywhere ubuntu
# packages might look for it, invcluding the current process

ENV['LANG'] = "en_US.UTF-8"
ENV['LC_ALL'] = "en_US.UTF-8"

template "/etc/default/locale" do
  source "locale"
  owner "root"
  group "root"
  mode 0644
end