ExtraRoute plugin for OpenStack Heat
====================================

This plugin enable using ExtraRoute as a resource in a Heat template.

### 1. Install the ExtraRoute plugin in Heat

NOTE: Heat scans several directories to find plugins. The list of directories
is specified in the configuration file "heat.conf" with the "plugin_dirs"
directive.

### 2. Restart heat

Only the process "heat-engine" needs to be restarted to load the newly installed
plugin.

### 3. Example of ExtraRoute

"router_extraroute": {
  "Type": "OS::Neutron::ExtraRoute",
  "Properties": {
    "router_id": { "Ref" : "router" },
    "destination": "172.16.0.0/24",
    "nexthop": "192.168.0.254"
  }
}

