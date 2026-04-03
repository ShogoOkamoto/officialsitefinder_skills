"""Tests for extract_address_tool.

Covers:
  1. Basic city-level extraction
  2. Street-number truncation (banchi omitted even when present in text)
  3. All prefecture suffix types (都/道/府/県)
  4. County (郡) handling
  5. Two-layer city+ward (市+区)
  6. Multiple addresses and deduplication
  7. Edge cases (empty text, no match, particles)
  8. extract_addresses_list and extract_addresses_detailed
"""

import json
import pytest
from extract_address_tool import (
    extract_addresses,
    extract_addresses_list,
    extract_addresses_detailed,
)


# ===========================================================================
# 1. Basic city-level extraction
# ===========================================================================

class TestBasicExtraction:

    def test_single_ward(self):
        result = json.loads(extract_addresses("本社は東京都渋谷区にあります。"))
        assert result == ["東京都渋谷区"]

    def test_single_city(self):
        result = json.loads(extract_addresses("大阪府大阪市の店舗です。"))
        assert result == ["大阪府大阪市"]

    def test_city_with_ward(self):
        result = json.loads(extract_addresses("京都府京都市中京区にある寺院。"))
        assert result == ["京都府京都市中京区"]

    def test_town(self):
        result = json.loads(extract_addresses("青森県上北郡六戸町に住んでいます。"))
        assert result == ["青森県上北郡六戸町"]

    def test_village(self):
        result = json.loads(extract_addresses("長野県下高井郡山ノ内町の温泉。"))
        assert len(json.loads(extract_addresses("長野県下高井郡山ノ内町の温泉。"))) >= 1

    def test_hokkaido_city_ward(self):
        result = json.loads(extract_addresses("北海道札幌市中央区の施設。"))
        assert result == ["北海道札幌市中央区"]


# ===========================================================================
# 2. Street-number truncation (key differentiator from extract_full_address_tool)
# ===========================================================================

class TestBanchiTruncation:

    def test_choume_banchi_go_truncated(self):
        """Banchi and go are NOT included in output."""
        result = json.loads(extract_addresses("東京都渋谷区道玄坂1丁目2番3号に所在。"))
        assert result == ["東京都渋谷区"]

    def test_hyphenated_truncated(self):
        """Hyphenated street numbers are NOT included."""
        result = json.loads(extract_addresses("東京都新宿区西新宿2-8-1が所在地。"))
        assert result == ["東京都新宿区"]

    def test_city_ward_banchi_truncated(self):
        """City+ward with banchi: only city+ward returned."""
        result = json.loads(extract_addresses("大阪府大阪市北区梅田2-4-9にあります。"))
        assert result == ["大阪府大阪市北区"]

    def test_banchi_only_truncated(self):
        """Simple banchi without choume: city level only."""
        result = json.loads(extract_addresses("神奈川県横浜市中区山下町1番地が住所です。"))
        assert result == ["神奈川県横浜市中区"]

    def test_full_address_returns_city_only(self):
        """Even with a full address, only city/ward returned."""
        result = json.loads(
            extract_addresses("東京都渋谷区道玄坂一丁目二番三号")
        )
        assert result == ["東京都渋谷区"]


# ===========================================================================
# 3. All prefecture suffix types
# ===========================================================================

class TestPrefecttureSuffixes:

    def test_to_tokyo(self):
        result = json.loads(extract_addresses("東京都千代田区"))
        assert "東京都千代田区" in result

    def test_do_hokkaido(self):
        result = json.loads(extract_addresses("北海道函館市"))
        assert "北海道函館市" in result

    def test_fu_osaka(self):
        result = json.loads(extract_addresses("大阪府堺市"))
        assert "大阪府堺市" in result

    def test_fu_kyoto(self):
        result = json.loads(extract_addresses("京都府宇治市"))
        assert "京都府宇治市" in result

    def test_ken_various(self):
        for addr in ["神奈川県横浜市", "愛知県名古屋市", "沖縄県那覇市", "福岡県福岡市"]:
            result = json.loads(extract_addresses(addr))
            assert addr in result


# ===========================================================================
# 4. County (郡) handling
# ===========================================================================

class TestCounty:

    def test_gun_town(self):
        result = json.loads(extract_addresses("青森県上北郡六戸町"))
        assert "青森県上北郡六戸町" in result

    def test_gun_village(self):
        result = json.loads(extract_addresses("群馬県吾妻郡草津町"))
        assert "群馬県吾妻郡草津町" in result

    def test_gun_excluded_from_city_field(self):
        """Detailed output should separate county from city."""
        result = json.loads(extract_addresses_detailed("青森県上北郡六戸町"))
        assert result[0]["prefecture"] == "青森県"
        assert result[0]["county"] == "上北郡"
        assert result[0]["city"] == "六戸町"


# ===========================================================================
# 5. Multiple addresses and deduplication
# ===========================================================================

class TestMultipleAndDedup:

    def test_multiple_addresses(self):
        text = "本社は東京都渋谷区にあります。支社は大阪府大阪市北区にあります。"
        result = json.loads(extract_addresses(text))
        assert len(result) == 2
        assert "東京都渋谷区" in result
        assert "大阪府大阪市北区" in result

    def test_deduplication(self):
        text = "東京都渋谷区にある店舗と、東京都渋谷区の別店舗。"
        result = json.loads(extract_addresses(text))
        assert result.count("東京都渋谷区") == 1

    def test_five_prefectures(self):
        text = "福岡県福岡市、北海道札幌市、沖縄県那覇市、神奈川県横浜市、愛知県名古屋市"
        result = json.loads(extract_addresses(text))
        assert len(result) == 5


# ===========================================================================
# 6. Edge cases
# ===========================================================================

class TestEdgeCases:

    def test_empty_string(self):
        result = json.loads(extract_addresses(""))
        assert result == []

    def test_no_address(self):
        result = json.loads(extract_addresses("これは住所を含まないテキストです。"))
        assert result == []

    def test_particle_not_over_matched(self):
        """Trailing particle 'に' should not be included in address."""
        text = "東京都渋谷区に行きます。"
        result = json.loads(extract_addresses(text))
        assert result == ["東京都渋谷区"]
        assert all(not a.endswith("に") for a in result)

    def test_whitespace_surrounding_address(self):
        """Whitespace around (not within) an address does not prevent extraction."""
        result = json.loads(extract_addresses("  東京都渋谷区  道玄坂1丁目  "))
        assert "東京都渋谷区" in result


# ===========================================================================
# 7. extract_addresses_list
# ===========================================================================

class TestExtractAddressesList:

    def test_returns_list(self):
        result = extract_addresses_list("東京都渋谷区にあります。")
        assert isinstance(result, list)
        assert result == ["東京都渋谷区"]

    def test_empty_returns_empty_list(self):
        assert extract_addresses_list("") == []


# ===========================================================================
# 8. extract_addresses_detailed
# ===========================================================================

class TestExtractAddressesDetailed:

    def test_ward_structure(self):
        result = json.loads(extract_addresses_detailed("東京都渋谷区にあります。"))
        assert len(result) == 1
        obj = result[0]
        assert obj["full_address"] == "東京都渋谷区"
        assert obj["prefecture"] == "東京都"
        assert obj["county"] is None
        assert obj["city"] == "渋谷区"

    def test_city_structure(self):
        result = json.loads(extract_addresses_detailed("大阪府大阪市の施設。"))
        obj = result[0]
        assert obj["full_address"] == "大阪府大阪市"
        assert obj["prefecture"] == "大阪府"
        assert obj["city"] == "大阪市"
        assert obj["county"] is None

    def test_city_ward_structure(self):
        result = json.loads(extract_addresses_detailed("大阪府大阪市北区梅田2-4-9"))
        obj = result[0]
        assert obj["full_address"] == "大阪府大阪市北区"
        assert obj["city"] == "大阪市北区"

    def test_county_structure(self):
        result = json.loads(extract_addresses_detailed("青森県上北郡六戸町"))
        obj = result[0]
        assert obj["prefecture"] == "青森県"
        assert obj["county"] == "上北郡"
        assert obj["city"] == "六戸町"

    def test_no_street_number_key(self):
        """Detailed output should NOT have street_number key."""
        result = json.loads(extract_addresses_detailed("東京都渋谷区道玄坂1丁目2番3号"))
        obj = result[0]
        assert "street_number" not in obj

    def test_empty_returns_empty_list(self):
        result = json.loads(extract_addresses_detailed(""))
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
