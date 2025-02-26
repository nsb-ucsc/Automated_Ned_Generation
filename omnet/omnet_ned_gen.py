import yaml


class OmnetNetworkGenerator:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config_data = None

    def load_config(self):
        """Load configuration data from a YAML file."""
        with open(self.config_file, 'r') as file:
            self.config_data = yaml.safe_load(file)

    def generate_ned_file(self):
        """Generate a complete NED file based on the configuration data."""
        if not self.config_data:
            raise ValueError("Configuration data is not loaded.")

        ned_lines = []

        # Add custom module definitions
        ned_lines.append(self.generate_module_definitions())
        ned_lines.append(self.generate_channel_definitions())

        # Begin the network definition
        ned_lines.append(f'network {self.config_data["network_name"]} {{')
        ned_lines.append(f'    parameters:')
        ned_lines.append(f'        @display("{self.config_data.get("display", "bgb=800,600")}");')

        # Add submodules
        ned_lines.append(f'    submodules:')
        for node in self.config_data['nodes']:
            ned_lines.append(f'        {node["name"]}: {self.get_node_type(node["role"])} {{')
            ned_lines.append(f'            @display("{node.get("display", "p=100,100")}");')
            ned_lines.append(f'        }}')

        # Add connections
        ned_lines.append(f'    connections:')
        for conn in self.config_data['connections']:
            src, dest = conn['src'], conn['dest']
            link_type = self.get_link_type(conn)
            ned_lines.append(f'        {src}.out++ --> {link_type} --> {dest}.in++;')

        # Close the network block
        ned_lines.append(f'}}')

        return '\n'.join(ned_lines)

    def generate_module_definitions(self):
        """Generate definitions for SourceNode, SinkNode, and RelayNode."""
        return """
simple SourceNode {
    parameters:
        @display("i=block/source");
    gates:
        output out[];
        input in[];
}

simple SinkNode {
    parameters:
        @display("i=block/sink");
    gates:
        output out[];
        input in[];
}

simple RelayNode {
    parameters:
        @display("i=block/relay");
    gates:
        output out[];
        input in[];
}
"""

    def generate_channel_definitions(self):
        """Generate definitions for WirelessLink and WiredLink."""
        return """
channel WirelessLink extends ned.DatarateChannel {
    parameters:
        delay = 100ms;
        datarate = 1Mbps;
}

channel WiredLink extends ned.DatarateChannel {
    parameters:
        delay = 10ms;
        datarate = 100Mbps;
}
"""

    def get_node_type(self, role):
        """Return the node type based on the role."""
        if role == 'source':
            return "SourceNode"
        elif role == 'sink':
            return "SinkNode"
        elif role == 'relay':
            return "RelayNode"
        else:
            return "SourceNode"  # Default to SourceNode if unknown

    def get_link_type(self, conn):
        """Return the link type based on the connection's network type."""
        if conn.get('network_type') == 'wireless':
            return "WirelessLink"
        elif conn.get('network_type') == 'wired':
            return "WiredLink"
        else:
            return "WiredLink"  # Default to WiredLink if unknown

    def write_ned_file(self, output_file, ned_content):
        """Write the generated NED content to a file."""
        with open(output_file, 'w') as file:
            file.write(ned_content)

    def run(self, output_file):
        """Execute the generator."""
        self.load_config()
        ned_content = self.generate_ned_file()
        self.write_ned_file(output_file, ned_content)
        print(f"NED file generated and saved to {output_file}")


# Example usage:
config_file = 'config_omnet_example.yaml'
output_file = 'example_omnet_research.ned'

generator = OmnetNetworkGenerator(config_file)
generator.run(output_file)
