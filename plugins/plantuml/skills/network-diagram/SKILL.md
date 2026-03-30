---
name: network-diagram
disable-model-invocation: true
description: This skill provides PlantUML network diagram (nwdiag) syntax reference. Use when writing, creating, or debugging PlantUML network diagrams. Applies when users mention "network diagram", "nwdiag", "network topology", "IP address", "subnet", "VLAN", "server rack", or need to diagram network infrastructure, topology, or connectivity in PlantUML.
---

> Source: https://plantuml.com/nwdiag

# PlantUML Network Diagram Reference

## Basic Network Definition

Define a network with a name and optional address. Servers are listed inside the network block with optional addresses.

```plantuml
@startnwdiag
nwdiag {
  network dmz {
    address = "210.x.x.x/24"

    web01 [address = "210.x.x.1"];
    web02 [address = "210.x.x.2"];
  }
}
@endnwdiag
```

## Multiple Networks

Nodes appearing in multiple networks are automatically connected across them.

```plantuml
@startnwdiag
nwdiag {
  network dmz {
    address = "210.x.x.x/24"

    web01 [address = "210.x.x.1"];
    web02 [address = "210.x.x.2"];
  }

  network internal {
    address = "172.x.x.x/24";

    web01 [address = "172.x.x.1"];
    web02 [address = "172.x.x.2"];
    db01;
    db02;
  }
}
@endnwdiag
```

## Multiple Addresses

Assign multiple addresses to a node by separating them with commas.

```plantuml
@startnwdiag
nwdiag {
  network dmz {
    address = "210.x.x.x/24"

    web01 [address = "210.x.x.1, 210.x.x.20"];
    web02 [address = "210.x.x.2"];
  }
}
@endnwdiag
```

## Grouping Nodes

### Groups Inside Networks

Groups can be defined within a network block to visually cluster related servers.

```plantuml
@startnwdiag
nwdiag {
  network Sample_front {
    address = "192.168.10.0/24";

    group web {
      web01 [address = ".1"];
      web02 [address = ".2"];
    }
  }

  network Sample_back {
    address = "192.168.20.0/24";

    web01 [address = ".1"];
    web02 [address = ".2"];
    db01 [address = ".101"];
    db02 [address = ".102"];

    group db {
      db01;
      db02;
    }
  }
}
@endnwdiag
```

### Groups Outside Networks

Groups defined at the top level span across all networks the member nodes belong to.

```plantuml
@startnwdiag
nwdiag {
  group {
    color = "#FFAAAA";
    web01;
    web02;
    db01;
  }

  network dmz {
    web01;
    web02;
  }

  network internal {
    web01;
    web02;
    db01;
    db02;
  }
}
@endnwdiag
```

### Group Properties

Groups support `color` and `description` properties.

```plantuml
@startnwdiag
nwdiag {
  group {
    color = "#CCFFCC";
    description = "Long group description";
    web01;
    web02;
    db01;
  }

  network dmz {
    web01;
    web02;
  }

  network internal {
    web01;
    web02;
    db01 [address = ".101", shape = database];
  }
}
@endnwdiag
```

## Peer Networks

Use `--` to create direct peer-to-peer connections outside of a network block.

```plantuml
@startnwdiag
nwdiag {
  inet [shape = cloud];
  inet -- router;

  network {
    router;
    web01;
    web02;
  }
}
@endnwdiag
```

### Peer Networks with Groups

```plantuml
@startnwdiag
nwdiag {
  internet [shape = cloud];
  internet -- router;

  network proxy {
    router;
    app;
  }

  group {
    color = "pink";
    app;
    db;
  }

  network default {
    app;
    db;
  }
}
@endnwdiag
```

## Colors

### Network Colors

Assign a color to a network using the `color` property.

```plantuml
@startnwdiag
nwdiag {
  network dmz {
    color = "pink"
    web01;
    web02;
  }

  network internal {
    color = "LightBlue"
    web01;
    web02;
    db01 [shape = database];
  }
}
@endnwdiag
```

### Combining Colors on Networks, Groups, and Nodes

```plantuml
@startnwdiag
nwdiag {
  group {
    color = "#7777FF";
    web01;
    web02;
    db01;
  }

  network dmz {
    color = "pink"
    web01;
    web02;
  }

  network internal {
    web01;
    web02;
    db01 [shape = database];
  }

  network internal2 {
    color = "LightBlue";
    web01;
    web02;
    db01;
  }
}
@endnwdiag
```

## Descriptions

Use the `description` property on nodes to add text labels below icons. Supports `\n` for line breaks.

```plantuml
@startnwdiag
nwdiag {
  network dmz {
    address = "210.x.x.x/24"

    web01 [address = "210.x.x.1", description = "Web Server 01"];
    web02 [address = "210.x.x.2", description = "Web Server 02"];
  }

  network internal {
    address = "172.x.x.x/24";

    web01 [address = "172.x.x.1"];
    web02 [address = "172.x.x.2"];
    db01 [address = "172.x.x.100", description = "Primary DB"];
    db02 [address = "172.x.x.101", description = "Replica DB"];
  }
}
@endnwdiag
```

## Shapes

Nodes support various shapes. Common shapes for network diagrams include: `cloud`, `database`, `node`, `actor`, `agent`, `artifact`, `boundary`, `card`, `collections`, `component`, `control`, `entity`, `file`, `folder`, `frame`, `hexagon`, `interface`, `label`, `package`, `person`, `queue`, `stack`, `rectangle`, `storage`, `usecase`.

```plantuml
@startnwdiag
nwdiag {
  network Sample_front {
    address = "192.168.10.0/24"

    group web {
      web01 [address = ".1, .2", shape = node]
      web02 [address = ".2, .3"]
    }
  }

  network Sample_back {
    address = "192.168.20.0/24"
    color = "palegreen"

    web01 [address = ".1"]
    web02 [address = ".2"]
    db01 [address = ".101", shape = database]
    db02 [address = ".102"]

    group db {
      db01;
      db02;
    }
  }
}
@endnwdiag
```

## Network Width Control

Use `width = full` to force a network to span the full width of the diagram.

```plantuml
@startnwdiag
nwdiag {
  network NETWORK_BASE {
    width = full
    dev_A [address = "dev_A"]
    dev_B [address = "dev_B"]
  }

  network IntNET1 {
    width = full
    dev_B [address = "dev_B1"]
    dev_M [address = "dev_M1"]
  }

  network IntNET2 {
    dev_B [address = "dev_B2"]
    dev_M [address = "dev_M2"]
  }
}
@endnwdiag
```

## Internal / Direct Connections (TCP/IP, USB, SERIAL)

Use `--` between nodes to create direct connections outside of a named network, useful for USB, serial, or other point-to-point links.

```plantuml
@startnwdiag
nwdiag {
  network LAN1 {
    a [address = "a1"];
  }

  network LAN2 {
    a [address = "a2"];
    switch [address = "s2"];
  }

  switch -- equip;
  equip [address = "e3"];
  equip -- printer;
  printer [address = "USB"];
}
@endnwdiag
```

## Using Sprites and Icons

### Standard Library Sprites

```plantuml
@startnwdiag
!include <office/Servers/application_server>
!include <office/Servers/database_server>

nwdiag {
  network dmz {
    address = "210.x.x.x/24"

    web01 [address = "210.x.x.1, 210.x.x.20",
           description = "<$application_server>\n web01"]
    web02 [address = "210.x.x.2",
           description = "<$application_server>\n web02"];
  }

  network internal {
    address = "172.x.x.x/24";

    web01 [address = "172.x.x.1"];
    web02 [address = "172.x.x.2"];
    db01 [address = "172.x.x.100",
          description = "<$database_server>\n db01"];
    db02 [address = "172.x.x.101",
          description = "<$database_server>\n db02"];
  }
}
@endnwdiag
```

### OpenIconic Icons

Use `<&icon_name>` syntax. Append `*scale` to resize (e.g., `<&cog*4>`).

```plantuml
@startnwdiag
nwdiag {
  group nightly {
    color = "#FFAAAA";
    description = "<&clock> Restarted nightly <&clock>";
    web02;
    db01;
  }

  network dmz {
    address = "210.x.x.x/24"

    user [description = "<&person*4.5>\n user1"];
    web01 [address = "210.x.x.1, 210.x.x.20",
           description = "<&cog*4>\nweb01"]
    web02 [address = "210.x.x.2",
           description = "<&cog*4>\nweb02"];
  }

  network internal {
    address = "172.x.x.x/24";

    web01 [address = "172.x.x.1"];
    web02 [address = "172.x.x.2"];
    db01 [address = "172.x.x.100",
          description = "<&spreadsheet*4>\n db01"];
    db02 [address = "172.x.x.101",
          description = "<&spreadsheet*4>\n db02"];
    ptr [address = "172.x.x.110",
         description = "<&print*4>\n ptr01"];
  }
}
@endnwdiag
```

## Title, Caption, Header, Footer, and Legend

Add document-level annotations around the diagram.

```plantuml
@startnwdiag
header some header
footer some footer
title My title

nwdiag {
  network inet {
    web01 [shape = cloud]
  }
}

legend
  The legend
end legend

caption This is caption
@endnwdiag
```

## Shadow Control

Disable shadows using the `<style>` block.

```plantuml
@startnwdiag
<style>
root {
  shadowing 0
}
</style>

nwdiag {
  network nw {
    server;
    internet;
  }

  internet [shape = cloud];
}
@endnwdiag
```

## Global Styling with Style Block

Customize the appearance of all diagram elements using `<style>`.

```plantuml
@startnwdiag
<style>
nwdiagDiagram {
  network {
    BackGroundColor green
    LineColor red
    LineThickness 1.0
    FontSize 18
    FontColor navy
  }
  server {
    BackGroundColor pink
    LineColor yellow
    LineThickness 1.0
    FontSize 18
    FontColor #blue
  }
  arrow {
    FontSize 17
    FontColor #red
    FontName Monospaced
    LineColor black
  }
  group {
    BackGroundColor cadetblue
    LineColor black
    LineThickness 2.0
    FontSize 11
    FontStyle bold
    Margin 5
    Padding 5
  }
}
</style>

nwdiag {
  network DMZ {
    address = "y.x.x.x/24"
    web01 [address = "y.x.x.1"];
    web02 [address = "y.x.x.2"];
  }

  network Internal {
    web01;
    web02;
    db01 [address = "w.w.w.z", shape = database];
  }

  group {
    description = "long group label";
    web01;
    web02;
    db01;
  }
}
@endnwdiag
```

## Comprehensive Example

A full example combining multiple features: networks, groups, colors, shapes, addresses, and descriptions.

```plantuml
@startnwdiag
title Corporate Network Topology

nwdiag {
  internet [shape = cloud];
  internet -- firewall;

  network dmz {
    address = "10.0.1.0/24"
    color = "#FFDDDD"

    firewall [address = "10.0.1.1", description = "Firewall\nCisco ASA"];
    web01 [address = "10.0.1.10", description = "Web Server 1"];
    web02 [address = "10.0.1.11", description = "Web Server 2"];
  }

  network app_net {
    address = "10.0.2.0/24"
    color = "#DDFFDD"

    web01 [address = "10.0.2.10"];
    web02 [address = "10.0.2.11"];
    app01 [address = "10.0.2.20", description = "App Server 1"];
    app02 [address = "10.0.2.21", description = "App Server 2"];
  }

  network db_net {
    address = "10.0.3.0/24"
    color = "#DDDDFF"

    app01 [address = "10.0.3.20"];
    app02 [address = "10.0.3.21"];
    db_primary [address = "10.0.3.100", shape = database, description = "Primary DB"];
    db_replica [address = "10.0.3.101", shape = database, description = "Replica DB"];
  }

  group web_tier {
    color = "#FFCCCC";
    description = "Web Tier";
    web01;
    web02;
  }

  group app_tier {
    color = "#CCFFCC";
    description = "Application Tier";
    app01;
    app02;
  }

  group data_tier {
    color = "#CCCCFF";
    description = "Data Tier";
    db_primary;
    db_replica;
  }
}
@endnwdiag
```
