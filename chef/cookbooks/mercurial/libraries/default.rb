def hgup_file
  return ::File.join(Chef::Config[:file_cache_path],"hgup")
end

def hg_connection_command
  case node['plateform']
  when "windows"
    cmd = ""
  else
    cmd = "--ssh 'ssh -i #{new_resource.key} -o StrictHostKeyChecking=no'"
  end
  return cmd
end
