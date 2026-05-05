from typer.testing import CliRunner

from mhxy_hp_overlay.cli import app


runner = CliRunner()


def test_damage_commands_do_not_expose_exclude_healing_option():
    for command in ("sum-damage", "analyze-damage-image", "watch-damage-screen"):
        result = runner.invoke(app, [command, "--help"])

        assert result.exit_code == 0
        assert "exclude-healing" not in result.output


def test_sum_damage_always_includes_healing_numbers():
    result = runner.invoke(
        app,
        ["sum-damage", "暴击 2388 +1042 1234/5678 -666 891", "--json"],
    )

    assert result.exit_code == 0
    assert '"total_damage": 4987' in result.output
    assert '"numbers": [2388, 1042, 666, 891]' in result.output
