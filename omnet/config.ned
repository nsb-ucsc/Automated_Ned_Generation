
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
}

channel WirelessLink extends ned.DatarateChannel {
    delay = 100ms;
    datarate = 1Mbps;
}
channel WiredLink extends ned.DatarateChannel {
    delay = 10ms;
    datarate = 100Mbps;
}
network EnterpriseWANExample {
    parameters:
        @display("bgb=1600,1200");
    submodules:
        hq_router: RouterNode {
            @display("p=400,300;is=vl");
        }
        ceo_workstation: SourceNode {
            @display("p=150,200;is=l");
        }
        finance_pc: SourceNode {
            @display("p=150,400;is=l");
        }
        branch_router: RouterNode {
            @display("p=1200,300;is=vl");
        }
        sales_laptop: SourceNode {
            @display("p=1400,200;is=l");
        }
        branch_printer: SinkNode {
            @display("p=1400,400;is=l");
        }
        dc_core_router: RouterNode {
            @display("p=800,800;is=vl");
        }
        auth_server: SinkNode {
            @display("p=650,950;is=l");
        }
        backup_server: SinkNode {
            @display("p=950,950;is=l");
        }
    connections:
        ceo_workstation.out++ --> WirelessLink --> hq_router.in++;
        finance_pc.out++ --> WiredLink --> hq_router.in++;
        sales_laptop.out++ --> WirelessLink --> branch_router.in++;
        branch_router.out++ --> WiredLink --> branch_printer.in++;
        dc_core_router.out++ --> WiredLink --> auth_server.in++;
        dc_core_router.out++ --> WiredLink --> backup_server.in++;
        hq_router.out++ --> WiredLink --> branch_router.in++;
        hq_router.out++ --> WiredLink --> dc_core_router.in++;
        branch_router.out++ --> WiredLink --> dc_core_router.in++;
}