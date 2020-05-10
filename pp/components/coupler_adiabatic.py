import picwriter.components as pc
from pp.ports import auto_rename_ports

from pp.components.waveguide_template import wg_strip
from pp.picwriter2component import picwriter2component
import pp


@pp.autoname
def coupler_adiabatic(
    length1=20.0,
    length2=50.0,
    length3=30.0,
    wg_sep=1.0,
    input_wg_sep=3.0,
    output_wg_sep=3.0,
    dw=0.1,
    waveguide_template=wg_strip,
    port=(0, 0),
    direction="EAST",
    **kwargs
):
    """ 50/50 adiabatic coupler
    Adiabatic Coupler Cell class.  Design based on asymmetric adiabatic 3dB coupler designs, such as those from https://doi.org/10.1364/CLEO.2010.CThAA2, https://doi.org/10.1364/CLEO_SI.2017.SF1I.5, and https://doi.org/10.1364/CLEO_SI.2018.STh4B.4.  Uses Bezier curves for the input, with poles set to half of the x-length of the S-bend.

    In this design, Region I is the first half of the input S-bend waveguide where the input waveguides widths taper by +dw and -dw, Region II is the second half of the S-bend waveguide with constant, unbalanced widths, Region III is the region where the two asymmetric waveguides gradually come together, Region IV is the coupling region where the waveguides taper back to the original width at a fixed distance from one another, and Region IV is the  output S-bend waveguide.

    Args:
        waveguide_template: object or function
        length1 (float): Length of the region that gradually brings the two assymetric waveguides together.  In this region the waveguide widths gradually change to be different by `dw`.
        length2 (float): Length of the coupling region, where the asymmetric waveguides gradually become the same width.
        length3 (float): Length of the output region where the two waveguides separate.
        wg_sep (float): Distance between the two waveguides, center-to-center, in the coupling region (Region 2).
        input_wg_sep (float): Separation of the two waveguides at the input, center-to-center.
        output_wg_sep (float): Separation of the two waveguides at the output, center-to-center.
        dw (float): Change in waveguide width.  In Region 1, the top arm tapers to the waveguide width+dw/2.0, bottom taper to width-dw/2.0.
        port (tuple): Cartesian coordinate of the input port (top left).  Defaults to (0,0).
        direction (string): Direction that the component will point *towards*, can be of type `'NORTH'`, `'WEST'`, `'SOUTH'`, `'EAST'`, OR an angle (float, in radians).  Defaults to 'EAST'.

    """

    c = pc.AdiabaticCoupler(
        pp.call_if_func(wg_strip, **kwargs),
        length1=length1,
        length2=length2,
        length3=length3,
        wg_sep=wg_sep,
        input_wg_sep=input_wg_sep,
        output_wg_sep=output_wg_sep,
        dw=dw,
        port=port,
        direction=direction,
    )

    c = picwriter2component(c)
    c = auto_rename_ports(c)
    pp.add_pins(c)
    return c


if __name__ == "__main__":
    import pp

    c = coupler_adiabatic(length3=5)
    print(c.ports)
    pp.show(c)
