from __future__ import annotations

import numpy as np

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import ComponentSpec, CrossSectionSpec, LayerSpec


def _compute_parameters(xs_bend, wrap_angle_deg, radius):
    r_bend = xs_bend.radius
    theta = wrap_angle_deg / 2.0
    size_x, dy = (
        r_bend * np.sin(theta * np.pi / 180),
        r_bend - r_bend * np.cos(theta * np.pi / 180),
    )
    bus_length = max(4 * size_x, 2 * radius)
    return (r_bend, size_x, dy, bus_length)


def _generate_bends(c, r_bend, wrap_angle_deg, cross_section):
    if wrap_angle_deg != 0:
        input_arc = gf.path.arc(radius=r_bend, angle=-wrap_angle_deg / 2.0)
        bend_middle_arc = gf.path.arc(radius=r_bend, angle=-wrap_angle_deg)

        bend_input_output = input_arc.extrude(cross_section=cross_section)

        bend_input = c << bend_input_output
        bend_middle = c << bend_middle_arc.extrude(cross_section=cross_section)
        bend_middle.d.rotate(180 + wrap_angle_deg / 2.0)

        bend_input.connect("o2", bend_middle.ports["o2"])

        bend_output = c << bend_input_output
        bend_output.connect("o2", bend_middle.ports["o1"], mirror=True)

        return (c, bend_input, bend_middle, bend_output)
    else:
        return (c, None, None, None)


def _generate_straights(c, bus_length, size_x, bend_input, bend_output, cross_section):
    straight_left = c << gf.components.straight(
        length=(bus_length - 4 * size_x) / 2.0, cross_section=cross_section
    )

    straight_right = c << gf.components.straight(
        length=(bus_length - 4 * size_x) / 2.0, cross_section=cross_section
    )

    if None not in (bend_input, bend_output):
        straight_left.connect("o2", bend_input.ports["o1"])

        straight_right.connect("o1", bend_output.ports["o1"])
    else:
        straight_left.connect("o2", straight_right.ports["o1"])

    return (c, straight_left, straight_right)


@gf.cell
def disk(
    radius: float = 10.0,
    gap: float = 0.2,
    wrap_angle_deg: float = 180.0,
    parity: int = 1,
    cross_section: CrossSectionSpec = "strip",
) -> Component:
    """Disk Resonator.

    Args:
       radius: disk resonator radius.
       gap: Distance between the bus straight and resonator.
       wrap_angle_deg: Angle in degrees between 0 and 180.
        determines how much the bus straight wraps along the resonator.
        0 corresponds to a straight bus straight.
        180 corresponds to a bus straight wrapped around half of the resonator.
       parity (1 or -1): 1, resonator left from bus straight, -1 resonator to the right.
       cross_section: cross_section spec.

    """
    if parity not in (1, -1):
        raise ValueError("parity must be 1 or -1")

    if wrap_angle_deg < 0.0 or wrap_angle_deg > 180.0:
        raise ValueError("wrap_angle_deg must be between 0.0 and 180.0")

    c = gf.Component()

    xs = gf.get_cross_section(cross_section=cross_section)
    radius_disk = radius
    radius = radius + xs.width / 2.0 + gap
    xs_bend = xs.copy(radius=radius)

    r_bend, size_x, dy, bus_length = _compute_parameters(
        xs_bend, wrap_angle_deg, radius
    )

    c, bend_input, bend_middle, bend_output = _generate_bends(
        c, r_bend, wrap_angle_deg, xs_bend
    )

    c, straight_left, straight_right = _generate_straights(
        c, bus_length, size_x, bend_input, bend_output, xs_bend
    )

    circle = c << gf.components.circle(radius=radius_disk, layer=xs.layer)

    circle_cladding = None
    if bend_middle is not None:
        dx = (bend_middle.ports["o1"].d.x + bend_middle.ports["o2"].d.x) / 2.0
        dy = straight_left.ports["o2"].d.y - 2 * dy + r_bend
        circle.d.move((dx, dy))
    else:
        circle.d.move(np.array(straight_left.ports["o2"].d.center) + (0, r_bend))

    if circle_cladding:
        circle_cladding.move(circle.center)

    c.add_port("o1", port=straight_left.ports["o1"])
    c.add_port("o2", port=straight_right.ports["o2"])
    xs.add_bbox(c)
    if parity == -1:
        c = c.rotate(180)

    c.flatten()
    return c


@gf.cell
def disk_heater(
    radius: float = 10.0,
    gap: float = 0.2,
    wrap_angle_deg: float = 180.0,
    parity: int = 1,
    cross_section: CrossSectionSpec = "strip",
    heater_layer: LayerSpec = "HEATER",
    via_stack: ComponentSpec = "via_stack_heater_mtop",
    heater_width: float = 5.0,
    heater_extent: float = 2.0,
    via_width: float = 10.0,
    port_orientation: float | None = 90,
) -> Component:
    """Disk Resonator with top metal heater.

    Args:
       radius: disk resonator radius.
       gap: Distance between the bus straight and resonator.
       wrap_angle_deg: Angle in degrees between 0 and 180.
        determines how much the bus straight wraps along the resonator.
        0 corresponds to a straight bus straight.
        180 corresponds to a bus straight wrapped around half of the resonator.
       parity (1 or -1): 1, resonator left from bus straight, -1 resonator to the right.
       cross_section: cross_section spec.
       heater_layer: layer of the heater.
       heater_width: width of the heater.
       heater_extent: length of heater beyond disk.
       via_width: size of the square via at the end of the heater.
       port_orientation: in degrees.
    """
    c = gf.Component()
    xs = gf.get_cross_section(cross_section=cross_section)

    disk_instance = c << disk(
        radius=radius,
        gap=gap,
        wrap_angle_deg=wrap_angle_deg,
        parity=parity,
        cross_section=cross_section,
    )

    dx = disk_instance.d.xmax - disk_instance.d.xmin
    dy = disk_instance.d.ymax - disk_instance.d.ymin
    heater = c << gf.get_component(
        gf.components.rectangle,
        size=(dx + 2 * heater_extent, heater_width),
        layer=heater_layer,
    )
    heater.d.x = disk_instance.d.x
    heater.d.y = dy / 2 + disk_instance.d.ymin + (xs.width + gap) / 2

    via = gf.get_component(via_stack, size=(via_width, via_width))
    c1 = c << via
    c2 = c << via
    c1.xmax = heater.xmin
    c1.y = heater.y
    c2.xmin = heater.xmax
    c2.y = heater.y
    c.add_ports(disk_instance.ports)
    c.add_ports(c1.ports.filter(orientation=port_orientation), prefix="e1")
    c.add_ports(c2.ports.filter(orientation=port_orientation), prefix="e2")
    c.auto_rename_ports()
    return c


if __name__ == "__main__":
    # c = disk_heater(wrap_angle_deg=75)
    c = disk_heater()
    c.show()
