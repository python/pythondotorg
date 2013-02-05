maintainer       "Opscode, Inc."
maintainer_email "cookbooks@opscode.com"
license          "Apache 2.0"
description      "Sets up the database master or slave"
long_description IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version          "1.1.0"

recipe "database", "Empty placeholder"
recipe "database::ebs_backup", "Considered deprecated, older way of backing up EBS volumes"
recipe "database::ebs_volume", "Sets up an EBS volume in EC2 for the database"
recipe "database::master", "Creates application specific user and database"
recipe "database::snapshot", "Locks tables and freezes XFS filesystem for replication, assumes EC2 + EBS"

depends "mysql", ">= 1.2.0"
depends "postgresql"
depends "aws"
depends "xfs"

%w{ debian ubuntu centos suse fedora redhat scientific }.each do |os|
  supports os
end
