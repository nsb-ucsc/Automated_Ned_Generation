import yaml
import sys
import os
from collections import defaultdict

class OmnetInetNetworkGenerator:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config_data = None
        self.gate_counters = defaultdict(lambda: defaultdict(int))

    def load_config(self):
        with open(self.config_file, 'r') as file:
            self.config_data = yaml.safe_load(file)

    def _get_gate_for_interface(self, node_name, interface_type):
        if interface_type in ['p2p', 'wired', 'csma']:
            gate_index = self.gate_counters[node_name]['eth']
            self.gate_counters[node_name]['eth'] += 1
            return f"{node_name}.ethg[{gate_index}]"
        elif interface_type == 'wifi':
            gate_index = self.gate_counters[node_name]['wlan']
            self.gate_counters[node_name]['wlan'] += 1
            return f"{node_name}.wlan[{gate_index}]"
        raise ValueError(f"Unknown interface type for gate assignment: {interface_type}")

    def generate_ned_file(self):
        cfg = self.config_data
        sim_cfg = cfg.get("simulation", {})
        network_name = sim_cfg.get("name", "MyInetNetwork")
        display_str = sim_cfg.get("display", "bgb=800,600")

        ned_lines = [
            'import inet.node.inet.StandardHost;',
            'import inet.node.inet.WirelessHost;',
            'import inet.node.inet.Router;',
            'import inet.node.ethernet.Eth100M;',
            'import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;',
            'import inet.physicallayer.wireless.common.medium.RadioMedium;',
            ''
        ]
        
        ned_lines.append(f'network {network_name} {{')
        ned_lines.append(f'    parameters:')
        ned_lines.append(f'        @display("{display_str}");')
        ned_lines.append(f'    submodules:')

        for node in cfg['nodes']:
            node_type = self.get_node_type(node)
            ned_lines.append(f'        {node["name"]}: {node_type} {{')
            ned_lines.append(f'            parameters:')
            ned_lines.append(f'                @display("{node.get("display", "p=100,100")}");')
            ned_lines.append(f'        }}')
        
        if 'globals' in cfg and 'omnet_inet' in cfg['globals']:
            inet_globals = cfg['globals']['omnet_inet']
            if 'medium' in inet_globals:
                medium = inet_globals['medium']
                ned_lines.append(f'        radioMedium: {medium["type"]} {{ @display("{medium.get("display", "p=500,400")}"); }}')
            if 'configurator' in inet_globals:
                configurator = inet_globals['configurator']
                ned_lines.append(f'        configurator: {configurator["type"]} {{ @display("{configurator.get("display", "p=500,500")}"); }}')

        ned_lines.append(f'    connections:')
        
        for conn in cfg['connections']:
            conn_type = conn['type']
            if conn_type in ['p2p', 'wired', 'csma']:
                ep1, ep2 = conn['endpoints']
                src_gate = self._get_gate_for_interface(ep1['node'], conn_type)
                dest_gate = self._get_gate_for_interface(ep2['node'], conn_type)
                
                params = conn.get("parameters", {})
                datarate = params.get("datarate", "100Mbps")
                link_type = f'Eth100M {{ datarate = {datarate}; }}'
                
                ned_lines.append(f'        {src_gate} <--> {link_type} <--> {dest_gate};')

        ned_lines.append(f'}}')
        return '\n'.join(ned_lines)

    def get_node_type(self, node):
        role = node['role']
        if role == 'source':
            if any(iface['type'] == 'wifi' for iface in node.get('interfaces', [])):
                return 'WirelessHost'
            return 'StandardHost'
        elif role == 'sink':
            return 'StandardHost'
        elif role == 'router':
            return 'Router'
        else:
            raise ValueError(f"Unknown role for INET node: {role}")

    def generate_ini_file(self):
        cfg = self.config_data
        sim_cfg = cfg.get("simulation", {})
        network_name = sim_cfg.get("name", "MyInetNetwork")
        
        ini_lines = [
            '[General]',
            f'network = {network_name}',
            f'sim-time-limit = {sim_cfg.get("duration", 60)}s',
            '',
            '# IPv4 Configuration',
            '*.configurator.config = xmldoc("config.xml", "/config/interface[contains(@hosts, substring-before(substring-after(ancestor-or-self::node/@moduleName, \'[\'), \']\'))]")',
            '*.configurator.addStaticRoutes = false',
            '*.configurator.addDefaultRoutes = true',
            '*.configurator.assignAddresses = true',
            '*.configurator.assignUniqueAddresses = true',
            '',
            '# Application Setup'
        ]

        traffic_flows = cfg.get("traffic_flows") or cfg.get("traffic", [])
        app_count = defaultdict(int)

        for flow in traffic_flows:
            src = flow['source']
            sink = flow['sink']
            params = flow.get('parameters', {})
            
            sink_app_idx = app_count[sink]
            ini_lines.append(f'*.{sink}.numApps = {sink_app_idx + 1}')
            ini_lines.append(f'*.{sink}.app[{sink_app_idx}].typename = "UdpSink"')
            ini_lines.append(f'*.{sink}.app[{sink_app_idx}].udp.localPort = {params.get("port", 5000 + sink_app_idx)}')
            app_count[sink] += 1
            
            src_app_idx = app_count[src]
            ini_lines.append(f'*.{src}.numApps = {src_app_idx + 1}')
            ini_lines.append(f'*.{src}.app[{src_app_idx}].typename = "UdpBasicApp"')
            ini_lines.append(f'*.{src}.app[{src_app_idx}].destAddresses = "{sink}"')
            ini_lines.append(f'*.{src}.app[{src_app_idx}].destPort = {params.get("port", 5000 + sink_app_idx)}')
            ini_lines.append(f'*.{src}.app[{src_app_idx}].messageLength = {params.get("packet_size", 1024)}B')
            
            rate_str = params.get("rate", "1Mbps").lower()
            if "mbps" in rate_str:
                rate_bps = float(rate_str.replace("mbps", "")) * 1_000_000
            elif "kbps" in rate_str:
                rate_bps = float(rate_str.replace("kbps", "")) * 1_000
            else:
                rate_bps = float(rate_str)

            packet_size_bytes = params.get("packet_size", 1024)
            send_interval = (packet_size_bytes * 8) / rate_bps if rate_bps > 0 else 1
            ini_lines.append(f'*.{src}.app[{src_app_idx}].sendInterval = {send_interval:.6f}s')
            
            ini_lines.append(f'*.{src}.app[{src_app_idx}].startTime = {params.get("start_time", 1)}s')
            app_count[src] += 1
            ini_lines.append('')
            
        return '\n'.join(ini_lines)

    def write_file(self, output_path, content):
        with open(output_path, 'w') as file:
            file.write(content)

    # This 'run' method is now corrected and robust.
    def run(self):
        self.load_config()
        
        sim_cfg = self.config_data.get("simulation", {})
        sim_name = sim_cfg.get("name", "MyInetNetwork")

        # Sanitize the simulation name to create a valid filename.
        def sanitize_filename(name):
            return "".join(c if c.isalnum() else "_" for c in name)

        output_basename = sanitize_filename(sim_name)

        # CORRECTED: These filenames have no path, so they will be created
        # in the current working directory set by the wrapper script.
        ned_filename = output_basename + ".ned"
        ini_filename = output_basename + ".ini"

        # Generate and write NED file
        ned_content = self.generate_ned_file()
        self.write_file(ned_filename, ned_content)
        print(f"INET NED file generated and saved to {os.path.abspath(ned_filename)}")

        # Generate and write INI file
        ini_content = self.generate_ini_file()
        self.write_file(ini_filename, ini_content)
        print(f"INET INI file generated and saved to {os.path.abspath(ini_filename)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 inet_omnet_gen.py <config.yaml>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    generator = OmnetInetNetworkGenerator(config_file)
    generator.run()