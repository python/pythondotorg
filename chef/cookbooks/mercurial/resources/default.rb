actions :sync, :clone

attribute :path, :kind_of => String, :name_attribute => true
attribute :repository, :kind_of => String, :required => true
attribute :reference, :kind_of => [Integer, String], :default => "tip"
attribute :key, :kind_of => String
attribute :owner, :kind_of => String
attribute :group, :kind_of => String
attribute :mode, :kind_of => String
