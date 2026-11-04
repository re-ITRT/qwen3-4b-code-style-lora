#pragma once

#include <algorithm>
#include <cmath>
#include <concepts>
#include <map>
#include <ranges>
#include <stdexcept>
#include <utility>
#include <vector>

class KNN {
public:
    explicit KNN(int n_neighbors = 5) : n_neighbors_(n_neighbors) {
        if (n_neighbors_ <= 0)
            throw std::invalid_argument("n_neighbors must be positive");
    }

    template <std::ranges::input_range XRange, std::ranges::input_range YRange>
        requires std::ranges::input_range<std::ranges::range_value_t<XRange>> &&
                 std::convertible_to<std::ranges::range_value_t<YRange>, double>
    KNN& fit(const XRange& X, const YRange& y) {
        auto [xc, yc] = check_X_y(X, y);
        x_ = std::move(xc);
        y_ = std::move(yc);
        classes_ = unique_labels(y_);
        fitted_ = true;
        return *this;
    }

    template <std::ranges::input_range XRange>
        requires std::ranges::input_range<std::ranges::range_value_t<XRange>>
    std::vector<double> predict(const XRange& X) const {
        check_is_fitted();
        return predict_impl(check_array(X));
    }

private:
    static std::vector<std::vector<double>> check_array(const auto& X) {
        std::vector<std::vector<double>> out;
        std::size_t cols = 0;
        for (const auto& row : X) {
            std::vector<double> r;
            for (const auto& v : row) r.push_back(static_cast<double>(v));
            if (out.empty()) cols = r.size();
            else if (r.size() != cols)
                throw std::invalid_argument("inconsistent feature shape");
            out.push_back(std::move(r));
        }
        if (out.empty()) throw std::invalid_argument("empty X");
        return out;
    }

    static auto check_X_y(const auto& X, const auto& y) {
        auto xc = check_array(X);
        std::vector<double> yc;
        for (auto v : y) yc.push_back(static_cast<double>(v));
        if (yc.size() != xc.size())
            throw std::invalid_argument("X/y length mismatch");
        return std::pair{std::move(xc), std::move(yc)};
    }

    static std::vector<double> unique_labels(const std::vector<double>& y) {
        auto out = y;
        std::sort(out.begin(), out.end());
        out.erase(std::unique(out.begin(), out.end()), out.end());
        return out;
    }

    void check_is_fitted() const {
        if (!fitted_) throw std::logic_error("KNN is not fitted");
    }

    std::vector<double> predict_impl(
        const std::vector<std::vector<double>>& X) const {
        std::vector<double> preds;
        preds.reserve(X.size());
        const auto k = std::min(
            static_cast<std::size_t>(n_neighbors_), x_.size());
        for (const auto& row : X) {
            std::vector<std::pair<double, std::size_t>> dists;
            dists.reserve(x_.size());
            for (std::size_t j = 0; j < x_.size(); ++j) {
                double d = 0.0;
                for (std::size_t f = 0; f < row.size(); ++f) {
                    double diff = row[f] - x_[j][f];
                    d += diff * diff;
                }
                dists.emplace_back(std::sqrt(d), j);
            }
            std::partial_sort(dists.begin(), dists.begin() + k, dists.end());

            std::map<double, int> votes;
            for (std::size_t i = 0; i < k; ++i)
                ++votes[y_[dists[i].second]];

            double best = 0.0;
            int best_count = -1;
            for (const auto& [label, count] : votes)
                if (count > best_count) { best = label; best_count = count; }
            preds.push_back(best);
        }
        return preds;
    }

    int n_neighbors_;
    bool fitted_ = false;
    std::vector<std::vector<double>> x_;
    std::vector<double> y_;
    std::vector<double> classes_;
};