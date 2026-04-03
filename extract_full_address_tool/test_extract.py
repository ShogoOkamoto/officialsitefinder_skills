"""Tests for Japanese full address extraction (including block/lot numbers)."""

import json
import pytest
from extract_full_address_tool.extract import (
    extract_full_addresses,
    extract_full_addresses_list,
    extract_full_addresses_detailed,
)


class TestExtractFullAddresses:
    """Test suite for extract_full_addresses function."""

    def test_choume_banchi_go(self):
        """Test: 丁目-番地-号 complete form."""
        text = "本社は東京都渋谷区道玄坂1丁目2番3号です。"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "東京都渋谷区道玄坂1丁目2番3号"

    def test_choume_hyphenated(self):
        """Test: 丁目 followed by hyphenated banchi/go."""
        text = "東京都渋谷区道玄坂1丁目2-3に行く。"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "東京都渋谷区道玄坂1丁目2-3"

    def test_pure_hyphenated_three(self):
        """Test: three-segment hyphenated (e.g. 2-8-1)."""
        text = "東京都新宿区西新宿2-8-1"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "東京都新宿区西新宿2-8-1"

    def test_pure_hyphenated_two(self):
        """Test: two-segment hyphenated (e.g. 2-4)."""
        text = "大阪府大阪市北区梅田2-4-9"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "大阪府大阪市北区梅田2-4-9"

    def test_banchi_only(self):
        """Test: banchi without go (番地)."""
        text = "神奈川県横浜市中区山下町1番地"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "神奈川県横浜市中区山下町1番地"

    def test_no_street_number(self):
        """Test: address without street number falls back to city/ward level."""
        text = "東京都渋谷区にある店舗"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "東京都渋谷区"

    def test_multiple_addresses_dedup(self):
        """Test: multiple addresses extracted; duplicates removed."""
        text = "支店A: 東京都渋谷区道玄坂1丁目2番3号、支店B: 大阪府大阪市北区梅田2-4-9、支店A再掲: 東京都渋谷区道玄坂1丁目2番3号"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 2
        assert "東京都渋谷区道玄坂1丁目2番3号" in addresses
        assert "大阪府大阪市北区梅田2-4-9" in addresses

    def test_all_prefecture_suffixes(self):
        """Test: 都/道/府/県 all handled correctly."""
        text = "東京都渋谷区1-2-3、北海道札幌市中央区1-2、京都府京都市中京区1番地、大阪府大阪市北区1丁目"
        addresses = json.loads(extract_full_addresses(text))
        assert any(a.startswith("東京都") for a in addresses)
        assert any(a.startswith("北海道") for a in addresses)
        assert any(a.startswith("京都府") for a in addresses)
        assert any(a.startswith("大阪府") for a in addresses)

    def test_county_gun(self):
        """Test: address with county (郡)."""
        text = "青森県上北郡六戸町字犬落瀬1-2"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert "青森県上北郡六戸町" in addresses[0]
        assert "1-2" in addresses[0]

    def test_city_ward_two_layer(self):
        """Test: market city + ward two-layer hierarchy."""
        text = "大阪府大阪市北区梅田2-4-9"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "大阪府大阪市北区梅田2-4-9"

    def test_empty_string(self):
        """Test: empty input returns empty array."""
        result = extract_full_addresses("")
        assert json.loads(result) == []

    def test_particle_not_over_matched(self):
        """Test: trailing particle (助詞) is not included in address."""
        text = "東京都渋谷区に行きます。大阪府大阪市で働きます。"
        addresses = json.loads(extract_full_addresses(text))
        assert "東京都渋谷区" in addresses
        assert "大阪府大阪市" in addresses
        # Particles should not be captured
        for addr in addresses:
            assert not addr.endswith("に")
            assert not addr.endswith("で")


class TestExtractFullAddressesList:
    """Test suite for extract_full_addresses_list function."""

    def test_returns_list(self):
        """Test that function returns a Python list."""
        text = "東京都渋谷区道玄坂1丁目2番3号"
        result = extract_full_addresses_list(text)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "東京都渋谷区道玄坂1丁目2番3号"

    def test_empty_returns_empty_list(self):
        """Test empty text returns empty list."""
        result = extract_full_addresses_list("")
        assert isinstance(result, list)
        assert len(result) == 0


class TestExtractFullAddressesDetailed:
    """Test suite for extract_full_addresses_detailed function."""

    def test_detailed_structure_with_street(self):
        """Test detailed output includes street_number field."""
        text = "東京都渋谷区道玄坂1丁目2番3号"
        addresses = json.loads(extract_full_addresses_detailed(text))
        assert len(addresses) == 1
        obj = addresses[0]
        assert obj["full_address"] == "東京都渋谷区道玄坂1丁目2番3号"
        assert obj["prefecture"] == "東京都"
        assert obj["city"] == "渋谷区"
        assert obj["county"] is None
        assert obj["street_number"] == "道玄坂1丁目2番3号"

    def test_detailed_structure_no_street(self):
        """Test detailed output when no street number; street_number is null."""
        text = "東京都渋谷区"
        addresses = json.loads(extract_full_addresses_detailed(text))
        assert len(addresses) == 1
        obj = addresses[0]
        assert obj["full_address"] == "東京都渋谷区"
        assert obj["street_number"] is None

    def test_detailed_with_county(self):
        """Test detailed output includes county field."""
        text = "青森県上北郡六戸町1-2"
        addresses = json.loads(extract_full_addresses_detailed(text))
        assert len(addresses) == 1
        obj = addresses[0]
        assert obj["prefecture"] == "青森県"
        assert obj["county"] == "上北郡"
        assert "六戸町" in obj["city"]

    def test_detailed_city_ward(self):
        """Test detailed output for city+ward two-layer."""
        text = "大阪府大阪市北区梅田2-4-9"
        addresses = json.loads(extract_full_addresses_detailed(text))
        assert len(addresses) == 1
        obj = addresses[0]
        assert obj["prefecture"] == "大阪府"
        assert obj["city"] == "大阪市北区"
        assert obj["street_number"] == "梅田2-4-9"

    def test_detailed_hyphenated(self):
        """Test detailed output for hyphenated street number."""
        text = "東京都新宿区西新宿2-8-1"
        addresses = json.loads(extract_full_addresses_detailed(text))
        assert len(addresses) == 1
        obj = addresses[0]
        assert obj["street_number"] == "西新宿2-8-1"

    def test_detailed_empty(self):
        """Test detailed output for empty input."""
        result = extract_full_addresses_detailed("")
        assert json.loads(result) == []


class TestNoPrefectureAddresses:
    """Test suite for addresses without prefecture (都道府県なし)."""

    def test_city_banchi(self):
        """市+番地（都道府県なし）を抽出できる。"""
        text = "横浜市中区山下町1番地"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "横浜市中区山下町1番地"

    def test_city_hyphenated(self):
        """市+ハイフン番地（都道府県なし）を抽出できる。"""
        text = "大阪市北区梅田2-4-9"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "大阪市北区梅田2-4-9"

    def test_ward_hyphenated(self):
        """区+ハイフン番地（都道府県なし）を抽出できる。"""
        text = "新宿区西新宿2-8-1"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "新宿区西新宿2-8-1"

    def test_town_hyphenated(self):
        """町+ハイフン番地（都道府県なし）を抽出できる。"""
        text = "六戸町犬落瀬1-2"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "六戸町犬落瀬1-2"

    def test_county_town_hyphenated(self):
        """郡+町+番地（都道府県なし）を抽出できる。"""
        text = "上北郡六戸町犬落瀬1-2"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert "六戸町" in addresses[0]
        assert "1-2" in addresses[0]

    def test_city_no_street_not_extracted(self):
        """都道府県なし・番地なしの市名単体は抽出されない（誤検出防止）。"""
        text = "横浜市について説明します。"
        addresses = json.loads(extract_full_addresses(text))
        assert addresses == []

    def test_ward_no_street_not_extracted(self):
        """都道府県なし・番地なしの区名単体は抽出されない（誤検出防止）。"""
        text = "渋谷区は東京都にあります。"
        addresses = json.loads(extract_full_addresses(text))
        # 都道府県あり形式の「東京都渋谷区」は取れるが「渋谷区」単体は取れない
        for addr in addresses:
            assert not addr == "渋谷区"

    def test_city_choume_banchi_go(self):
        """市+丁目番地号（都道府県なし）を抽出できる。"""
        text = "渋谷区道玄坂1丁目2番3号"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "渋谷区道玄坂1丁目2番3号"

    def test_detailed_prefecture_null(self):
        """都道府県なしの場合、detailed出力で prefecture が null になる。"""
        text = "大阪市北区梅田2-4-9"
        addresses = json.loads(extract_full_addresses_detailed(text))
        assert len(addresses) == 1
        obj = addresses[0]
        assert obj["prefecture"] is None
        assert obj["city"] == "大阪市北区"
        assert obj["street_number"] == "梅田2-4-9"

    def test_detailed_ward_prefecture_null(self):
        """区+番地の detailed 出力で prefecture が null になる。"""
        text = "新宿区西新宿2-8-1"
        addresses = json.loads(extract_full_addresses_detailed(text))
        assert len(addresses) == 1
        obj = addresses[0]
        assert obj["prefecture"] is None
        assert obj["city"] == "新宿区"
        assert obj["street_number"] == "西新宿2-8-1"

    def test_mixed_with_and_without_prefecture(self):
        """都道府県あり・なしが混在するテキストから両方抽出できる。"""
        text = "本社: 東京都新宿区西新宿2-8-1、支社: 横浜市中区山下町1番地"
        addresses = json.loads(extract_full_addresses(text))
        assert "東京都新宿区西新宿2-8-1" in addresses
        assert "横浜市中区山下町1番地" in addresses

    def test_sapporo_jou_style(self):
        """札幌形式（N条M丁目）の住所を郵便番号・前後テキスト混在でも抽出できる。"""
        text = "060-8543札幌市中央区南1条西16丁目291番地\n公共交通機関でお越しのかた"
        addresses = json.loads(extract_full_addresses(text))
        assert len(addresses) == 1
        assert addresses[0] == "札幌市中央区南1条西16丁目291番地"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
