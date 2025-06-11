import yaml
import sys
import os

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
        cfg = self.config_data
        
        sim_cfg = cfg.get("simulation", {})
        network_name = sim_cfg.get("name", "MyNetwork")
        display_str = sim_cfg.get("display", "bgb=800,600")

        ned_lines.append(self.generate_module_definitions())
        ned_lines.append(self.generate_channel_definitions())

        ned_lines.append(f'network {network_name} {{')
        ned_lines.append(f'    parameters:')
        ned_lines.append(f'        @display("{display_str}");')

        ned_lines.append(f'    submodules:')
        for node in cfg['nodes']:
            ned_lines.append(f'        {node["name"]}: {self.get_node_type(node["role"])} {{')
            ned_lines.append(f'            @display("{node.get("display", "p=100,100")}");')
            ned_lines.append(f'        }}')

        ned_lines.append(f'    connections:')
        for conn in cfg['connections']:
            src = conn['endpoints'][0]['node']
            dest = conn['endpoints'][1]['node']
            link_type = self.get_link_type(conn)
            ned_lines.append(f'        {src}.out++ --> {link_type} --> {dest}.in++;')

        ned_lines.append(f'}}')

        return '\n'.join(ned_lines)

    def generate_module_definitions(self):
        """Generate definitions for SourceNode, SinkNode, and RouterNode."""
        return """
simple SourceNode {
    parameters: @display("i=block/source");
    gates: output out[]; input in[];
}
simple SinkNode {
    parameters: @display("i=block/sink");
    gates: output out[]; input in[];
}
simple RouterNode {
    parameters: @display("i=block/routing");
    gates: output out[]; input in[];
}"""

    def generate_channel_definitions(self):
        """Generate definitions for WirelessLink and WiredLink."""
        return """
channel WirelessLink extends ned.DatarateChannel {
    delay = 100ms;
    datarate = 1Mbps;
}
channel WiredLink extends ned.DatarateChannel {
    delay = 10ms;
    datarate = 100Mbps;
}"""

    def get_node_type(self, role):
        """Return the node type based on the role."""
        if role == 'source': return "SourceNode"
        if role == 'sink': return "SinkNode"
        if role == 'router': return "RouterNode"
        return "SourceNode"  # Default

    def get_link_type(self, conn):
        """Return the link type based on the connection's type."""
        conn_type = conn.get('type')
        if conn_type == 'wifi':
            return "WirelessLink"
        elif conn_type == 'p2p':
            return "WiredLink"
        return "WiredLink"  # Default

    def write_ned_file(self, output_file, ned_content):
        """Write the generated NED content to a file."""
        with open(output_file, 'w') as file:
            file.write(ned_content)

    def run(self):
        """
        Execute the generator.
        Automatically determines the output filename from the 'name' key
        in the config file's 'simulation' section.
        """
        self.load_config()

        # Get simulation name from the config file itself.
        sim_cfg = self.config_data.get("simulation", {})
        sim_name = sim_cfg.get("name", "MyNetwork")

        # Sanitize the simulation name to create a valid filename.
        def sanitize_filename(name):
            return "".join(c if c.isalnum() else "_" for c in name)

        output_basename = sanitize_filename(sim_name)
        output_file = output_basename + ".ned"
        
        ned_content = self.generate_ned_file()
        self.write_ned_file(output_file, ned_content)
        print(f"NED file generated and saved to {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 omnet_ned_gen.py <config.yaml>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    generator = OmnetNetworkGenerator(config_file)
    generator.run()