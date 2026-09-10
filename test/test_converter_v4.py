import io
from lxml import objectify
import pathlib
import pytest
import tempfile

from hpxml_version_translator.converter import (
    convert_hpxml4_to_5,
    convert_hpxml_to_version,
)
from hpxml_version_translator import exceptions as exc

hpxml_dir = pathlib.Path(__file__).resolve().parent / "hpxml_v4_files"


def convert_hpxml_and_parse(input_filename, version="5.0"):
    with tempfile.NamedTemporaryFile("w+b") as f_out:
        convert_hpxml_to_version(version, input_filename, f_out)
        f_out.seek(0)
        root = objectify.parse(f_out).getroot()
    return root


def test_version_change_to_5():
    root = convert_hpxml_and_parse(hpxml_dir / "version_change.xml")
    assert root.attrib["schemaVersion"] == "5.0"


def test_not_present():
    root = convert_hpxml_and_parse(hpxml_dir / "not_present.xml")
    bldg_details = root.Building[0].BuildingDetails

    for i in (0, 1):
        fnd = bldg_details.Enclosure.Foundations.Foundation[i]
        assert fnd.FoundationType.BellyAndWing.BellyWrapCondition == "not present"

    roof = bldg_details.Enclosure.Roofs.Roof
    roof_ins_mat = roof.Insulation.Layer.InsulationMaterial
    assert hasattr(roof_ins_mat, "NotPresent")
    assert roof.InteriorFinish.Type == "not present"

    for i in (0, 1):
        wall = bldg_details.Enclosure.Walls.Wall[i]
        assert wall.Siding == "not present"
        assert wall.InteriorFinish.Type == "not present"
        wall_ins_mat = wall.Insulation.Layer.InsulationMaterial
        assert hasattr(wall_ins_mat, "NotPresent")

    rim_joist = bldg_details.Enclosure.RimJoists.RimJoist[0]
    rim_joist_ins_mat = rim_joist.Insulation.Layer.InsulationMaterial
    assert hasattr(rim_joist_ins_mat, "NotPresent")
    assert rim_joist.Siding == "not present"

    foundation_wall = bldg_details.Enclosure.FoundationWalls.FoundationWall[0]
    foundation_wall_ins_mat = foundation_wall.Insulation.Layer.InsulationMaterial
    assert hasattr(foundation_wall_ins_mat, "NotPresent")
    assert foundation_wall.InteriorFinish.Type == "not present"

    for i in (0, 1, 2):
        floor = bldg_details.Enclosure.Floors.Floor[i]
        assert floor.FloorCovering == "not present"
        assert floor.InteriorFinish.Type == "not present"
        if i > 0:
            floor_ins_mat = floor.Insulation.Layer.InsulationMaterial
            assert hasattr(floor_ins_mat, "NotPresent")

    slab = bldg_details.Enclosure.Slabs.Slab[0]
    slab_ins_mat = slab.PerimeterInsulation.Layer.InsulationMaterial
    assert hasattr(slab_ins_mat, "NotPresent")
    ext_horiz_ins_mat = slab.ExteriorHorizontalInsulation.Layer.InsulationMaterial
    assert hasattr(ext_horiz_ins_mat, "NotPresent")
    under_slab_ins_mat = slab.UnderSlabInsulation.Layer.InsulationMaterial
    assert hasattr(under_slab_ins_mat, "NotPresent")
    assert slab.FloorCovering == "not present"

    for i in (0, 1, 2):
        window = bldg_details.Enclosure.Windows.Window[i]
        skylight = bldg_details.Enclosure.Skylights.Skylight[i]
        if i == 0:
            assert window.ExteriorShading.Type == "not present"
            assert window.InteriorShading.Type == "not present"
            assert skylight.ExteriorShading.Type == "not present"
            assert skylight.InteriorShading.Type == "not present"
        elif i == 1:
            assert window.ExteriorShading.Type != "not present"
            assert window.InteriorShading.Type != "not present"
            assert skylight.ExteriorShading.Type != "not present"
            assert skylight.InteriorShading.Type != "not present"
        else:
            assert not hasattr(window, "ExteriorShading")
            assert not hasattr(window, "InteriorShading")
            assert not hasattr(skylight, "ExteriorShading")
            assert not hasattr(skylight, "InteriorShading")

    duct_ins_mat = (
        bldg_details.Systems.HVAC.HVACDistribution.DistributionSystemType.AirDistribution.Ducts.DuctInsulationMaterial
    )
    assert hasattr(duct_ins_mat, "NotPresent")

    for i in (0, 1):
        pool = bldg_details.Pools.Pool[i]
        spa = bldg_details.Spas.PermanentSpa[i]
        assert pool.Type == "not present"
        assert pool.Pumps.Pump[0].Type == "not present"
        assert pool.Pumps.Pump[1].Type == "not present"
        assert pool.Cleaner.Type == "not present"
        assert pool.Heater.Type == "not present"
        assert spa.Type == "not present"
        assert spa.Pumps.Pump[0].Type == "not present"
        assert spa.Pumps.Pump[1].Type == "not present"
        assert spa.Cleaner.Type == "not present"
        assert spa.Heater.Type == "not present"


def test_refrigerator_uncategorized():
    root = convert_hpxml_and_parse(hpxml_dir / "refrigerator_uncategorized.xml")

    for i in (0, 1, 2, 3):
        fridge = root.Building[0].BuildingDetails.Appliances.Refrigerator[i]
        if i in (0, 2):
            assert fridge.Type == "other"
        elif i == 1:
            assert not hasattr(fridge, "Type")
        elif i == 3:
            assert fridge.Type != "other"


def test_solar_tube():
    root = convert_hpxml_and_parse(hpxml_dir / "solar_tube.xml")

    for i in (0, 1, 2):
        skylight = root.Building[0].BuildingDetails.Enclosure.Skylights.Skylight[i]
        if i == 1:
            assert skylight.SkylightType == "tubular"
        else:
            assert not hasattr(skylight, "SkylightType")


def test_cool_roof():
    root = convert_hpxml_and_parse(hpxml_dir / "cool_roof.xml")

    for i in (0, 1, 2):
        roof = root.Building[0].BuildingDetails.Enclosure.Roofs.Roof[i]
        if i == 0:
            assert not hasattr(roof, "RoofType")
            assert not hasattr(roof, "CoolRoof")
        elif i == 1:
            assert roof.RoofType == "shingles"
            assert not hasattr(roof, "CoolRoof")
        elif i == 2:
            assert roof.CoolRoof == True


def test_mismatch_version():
    f_out = io.BytesIO()
    with pytest.raises(
        exc.HpxmlTranslationError,
        match=r"convert_hpxml4_to_5 must have valid target version of 5\.x",
    ):
        convert_hpxml4_to_5(hpxml_dir / "version_change.xml", f_out, "2.0")
