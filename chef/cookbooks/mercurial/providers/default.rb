action :sync do
  ::File.delete(hgup_file) if ::File.exist?(hgup_file)
  execute "sync repository #{new_resource.path}" do
    not_if "hg identify #{new_resource.path}"
    command "hg clone --rev #{new_resource.reference} #{hg_connection_command} #{new_resource.repository} #{new_resource.path} && touch #{hgup_file}"
    creates hgup_file
    notifies :run, "execute[set ownership]"
    notifies :run, "execute[set permissions]"
  end
  execute "check incoming changes" do
    command "hg incoming --rev #{new_resource.reference} #{hg_connection_command}  #{new_resource.repository} && touch #{hgup_file} || true"
    cwd new_resource.path
    creates hgup_file
    notifies :run, "execute[pull]"
  end
  execute "pull" do
    command "hg pull --rev #{new_resource.reference} #{hg_connection_command} #{new_resource.repository}"
    cwd new_resource.path
    only_if { ::File.exist?(hgup_file) }
    action :nothing
    notifies :run, "execute[update]"
  end
  execute "update" do
    command "hg update"
    cwd new_resource.path
    action :nothing
    notifies :run, "execute[set ownership]"
    notifies :run, "execute[set permissions]"
  end
  execute "set ownership" do
    command "chown -R #{new_resource.owner}:#{new_resource.group} #{new_resource.path}"
    action :nothing
  end
  if new_resource.mode then
    execute "set permissions" do
      command "chmod -R #{new_resource.mode} #{new_resource.path}"
    end
  end
  if ::File.exist?(hgup_file)
    new_resource.updated_by_last_action(true)
    ::File.delete(hgup_file)
  else
    new_resource.updated_by_last_action(false)
  end
end

action :clone do
  ::File.delete(hgup_file) if ::File.exist?(hgup_file)
  execute "clone repository #{new_resource.path}" do
    command "hg clone --rev #{new_resource.reference} #{hg_connection_command} #{new_resource.repository} #{new_resource.path} && touch #{hgup_file}"
    not_if "hg identify #{new_resource.path}"
    creates hgup_file
    notifies :run, "execute[set permission]"
    notifies :run, "execute[set ownership]"
  end
  execute "set ownership" do
    command "chown -R #{new_resource.owner}:#{new_resource.group} #{new_resource.path}"
    action :nothing
  end
  if new_resource.mode then
    execute "set permission" do
      command "chmod -R #{new_resource.mode} #{new_resource.path}"
    end
  end
  if ::File.exist?(hgup_file)
    new_resource.updated_by_last_action(true)
    ::File.delete(hgup_file)
  else
    new_resource.updated_by_last_action(false)
  end
end
