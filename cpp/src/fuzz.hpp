#pragma once
#include "levenshtein.hpp"
#include "utils.hpp"
#include <algorithm>
#include <cmath>
#include <string>
#include <vector>


float token_ratio(const std::string &a, const std::string &b) {
  std::vector<std::string_view> tokens_a = splitSV(a);
  std::sort(tokens_a.begin(), tokens_a.end());
  std::vector<std::string_view> tokens_b = splitSV(b);
  std::sort(tokens_b.begin(), tokens_b.end());

  float result = normalized_levenshtein(tokens_a, tokens_b);

  tokens_a.erase(std::unique(tokens_a.begin(), tokens_a.end()), tokens_a.end());
  tokens_b.erase(std::unique(tokens_b.begin(), tokens_b.end()), tokens_b.end());

  auto intersection = intersection_count_sorted_vec(tokens_a, tokens_b);

  size_t ab_len = joinedStringViewLength(intersection.ab);
  size_t ba_len = joinedStringViewLength(intersection.ba);

  if (!ab_len || !ba_len) {
    return 1.0;
  }

  size_t double_prefix = 2 * joinedStringViewLength(intersection.ba);
  if (double_prefix) {
    ++ab_len;
    ++ba_len;
  }

  result = std::max(result,
    (float)1.0 - (float)ab_len / (float)(ab_len + double_prefix));
  result = std::max(result,
    (float)1.0 - (float)ba_len / (float)(ba_len + double_prefix));
  size_t lensum = ab_len + ba_len + double_prefix;
  return std::max(result,
    (float)1.0 - levenshtein(intersection.ab, intersection.ba) / (float)lensum);
}


uint8_t full_ratio(const std::string &query, const std::string &choice,
                   uint8_t score_cutoff) {
  float sratio = normalized_levenshtein(query, choice);
  const float UNBASE_SCALE = 0.95;
  float min_ratio = std::max((float)score_cutoff / (float)100.0, sratio);
  if (min_ratio < UNBASE_SCALE) {
    sratio = std::max(sratio, token_ratio(query, choice) * UNBASE_SCALE);
  }
  return static_cast<uint8_t>(std::round(sratio * 100.0));
}


/*uint8_t partial_ratio(const std::string &query, const std::string &choice,
                      uint8_t partial_scale, uint8_t score_cutoff)
{
  float sratio = normalized_levenshtein(query, choice);
  float min_ratio = std::max(sratio, (float)score_cutoff / (float)100);
  if (min_ratio < partial_scale) {
    sratio = std::max(sratio, partial_string_ratio(query, choice) * partial_scale);
    min_ratio = std::max(sratio, min_ratio);
    const float UNBASE_SCALE = 0.95;
    if (min_ratio < UNBASE_SCALE * partial_scale) {
      sratio = std::max(sratio, partial_token_ratio(query, choice) * UNBASE_SCALE * partial_scale );
    }
  }
  return static_cast<uint8_t>(std::round(sratio * 100.0));
}*/


uint8_t ratio(const std::string &query, const std::string &choice,
              uint8_t score_cutoff) {
  if (query == choice) {
    return 100;
  }

  if (query.empty() || choice.empty() || score_cutoff == 100) {
    return 0;
  }

  size_t len_a = query.length();
  size_t len_b = choice.length();
  float len_ratio;
  if (len_a > len_b) {
    len_ratio = (float)len_a / (float)len_b;
  } else {
    len_ratio = (float)len_b / (float)len_a;
  }

  if (len_ratio < 1.5) {
    return full_ratio(query, choice, score_cutoff);
  // TODO: this is still missing
  } else if (len_ratio < 8.0) {
    return 0.0;
    // return partial_ratio(query, choice, 0.9, score_cutoff);
  } else {
    return 0.0;
    // return partial_ratio(query, choice, 0.6, score_cutoff);
  }
}