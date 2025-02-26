import yaml

class OmnetInetNetworkGenerator:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config_data = None

    def load_config(self):
        with open(self.config_file, 'r') as file:
            self.config_data = yaml.safe_load(file)

    def generate_ned_file(self):
        if not self.config_data:
            raise ValueError("Configuration data is not loaded.")

        ned_lines = []
        ned_lines.append(f'import inet.node.inet.WirelessHost;')
        ned_lines.append(f'import inet.node.inet.StandardHost;')
        ned_lines.append(f'import inet.physicallayer.wireless.common.medium.RadioMedium;')
        ned_lines.append(f'import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;')
        ned_lines.append(f'import inet.node.ethernet.Eth100M;')

        ned_lines.append('')
        ned_lines.append(f'network {self.config_data["network_name"]} {{')
        ned_lines.append(f'    parameters:')
        ned_lines.append(f'        @display("{self.config_data.get("display", "bgb=800,600")}");')
        ned_lines.append(f'    submodules:')

        for node in self.config_data['nodes']:
            node_type = self.get_node_type(node)
            ned_lines.append(f'        {node["name"]}: {node_type} {{')
            ned_lines.append(f'            @display("{node.get("display", "p=100,100")}");')
            ned_lines.append(f'        }}')

        ned_lines.append(f'        medium: RadioMedium {{')
        ned_lines.append(f'            @display("{self.config_data["medium"].get("display", "p=500,400")}");')
        ned_lines.append(f'        }}')
        ned_lines.append(f'        configurator: Ipv4NetworkConfigurator {{')
        ned_lines.append(f'            @display("{self.config_data["configurator"].get("display", "p=500,500")}");')
        ned_lines.append(f'        }}')
        ned_lines.append(f'    connections:')

        for conn in self.config_data['connections']:
            src, dest = conn['src'], conn['dest']
            link_type = self.get_link_type(conn)
            ned_lines.append(f'        {src} <--> {link_type} <--> {dest};')

        ned_lines.append(f'}}')
        return '\n'.join(ned_lines)

    def get_node_type(self, node):
        role = node.get('role')
        if role == 'source':
            return 'WirelessHost'
        elif role == 'sink':
            return 'WirelessHost'
        elif role == 'relay':
            return 'StandardHost'
        else:
            raise ValueError(f"Unknown role: {role}")

    def get_link_type(self, conn):
        network_type = conn.get('type')
        if network_type == 'WirelessLink':
            return 'WirelessLink'
        elif network_type == 'EthernetLink':
            return 'EthernetLink'
        else:
            raise ValueError(f"Unknown network type: {network_type}")

    def write_ned_file(self, output_file, ned_content):
        with open(output_file, 'w') as file:
            file.write(ned_content)

    def run(self, output_file):
        self.load_config()
        ned_content = self.generate_ned_file()
        self.write_ned_file(output_file, ned_content)
        print(f"NED file generated and saved to {output_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python3 omnet_inet_gen.py <config.yaml> <output.ned>")
        sys.exit(1)
    config_file = sys.argv[1]
    output_file = sys.argv[2]
    generator = OmnetInetNetworkGenerator(config_file)
    generator.run(output_file)
