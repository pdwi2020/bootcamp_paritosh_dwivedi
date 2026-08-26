# Homework 09: feature engineering

This homework builds three features on the SPY and VIX data explored in Stage 08, so each one answers a question the EDA actually raised rather than being invented in isolation.

## Files

- `homework09_feature-engineering_submission.ipynb` implements the features, gives the reasoning for each, and checks each against the target.
- `src/features.py` holds the reusable builders. `add_vol_ratio(frame, short=5, long=20)` divides short-window realised volatility by the longer window; `add_vix_spread(frame, window=20)` takes implied volatility net of trailing realised; `add_regime_dummies(frame)` one-hot encodes the VIX band; `add_forward_volatility(frame, horizon=5)` builds the forward-looking target. `TRADING_DAYS = 252` annualises, and `CALM_VIX, STRESSED_VIX = 15.0, 25.0` set the regime cut points.

## The three features and where they came from

`vol_ratio` follows from the EDA observation that volatility clusters. A ratio above one says the recent past is more turbulent than the trailing month, which is the shape of a regime turning before the level itself moves.

`vix_spread` follows from the relationship between implied and realised volatility. VIX is option-implied, so it carries a forward view that realised volatility cannot; the spread isolates that premium instead of letting the two correlated series compete in the model.

`regime_*` is the required categorical encoding. The VIX band is one-hot encoded rather than label encoded, because label encoding would impose a false ordinal arithmetic on the model, implying that stressed minus calm is a meaningful quantity. Frequency encoding was rejected for a different reason: it would let the sample composition of the training window leak into the feature definition.

Each feature is checked by correlation against the forward volatility target, with a sentence on what the number does and does not establish. Correlation here is a sanity check that the feature moves with the thing being predicted, not evidence of predictive power on unseen data.

Homework09 uses only `src/` under the course repository structure. The notebook acquires its data in memory rather than writing a snapshot, so there are no data folders.

Paritosh Dwivedi is the author and retains responsibility for understanding, validating, and presenting this work.
