import numpy as np
from scipy.stats import median_test

from flask_monitoringdashboard.core.reporting.questions.report_question import (
    Answer,
    ReportQuestion,
)
from flask_monitoringdashboard.database import session_scope

from flask_monitoringdashboard.database.request import get_latencies_sample


class MedianLatencyAnswer(Answer):
    def __init__(
        self,
        is_significant,
        comparison_interval_latencies_sample=None,
        compared_to_interval_latencies_sample=None,
        percentual_diff=None,
        comparison_interval_median=None,
        compared_to_interval_median=None,
    ):
        super().__init__('MEDIAN_LATENCY')

        self._is_significant = is_significant
        self._comparison_interval_latencies_sample = comparison_interval_latencies_sample
        self._compared_to_interval_latencies_sample = compared_to_interval_latencies_sample
        self._percentual_diff = percentual_diff

        self._compared_to_interval_median = compared_to_interval_median
        self._comparison_interval_median = comparison_interval_median

    def meta(self):
        return dict(
            latencies_sample=dict(
                comparison_interval=self._comparison_interval_latencies_sample,
                compared_to_interval=self._compared_to_interval_latencies_sample,
            ),
            comparison_median=self._comparison_interval_median,
            compared_to_median=self._compared_to_interval_median,
            percentual_diff=self._percentual_diff,
        )

    def is_significant(self):
        return self._is_significant


class MedianLatency(ReportQuestion):
    def get_answer(self, endpoint, comparison_interval, compared_to_interval):
        with session_scope() as db_session:
            comparison_interval_latencies_sample = get_latencies_sample(
                db_session, endpoint.id, comparison_interval
            )
            compared_to_interval_latencies_sample = get_latencies_sample(
                db_session, endpoint.id, compared_to_interval
            )

            if (
                min(
                    len(comparison_interval_latencies_sample),
                    len(compared_to_interval_latencies_sample),
                )
                == 0
            ):
                return MedianLatencyAnswer(
                    is_significant=False,
                    comparison_interval_latencies_sample=comparison_interval_latencies_sample,
                    compared_to_interval_latencies_sample=compared_to_interval_latencies_sample,
                )

            comparison_interval_median = float(np.median(comparison_interval_latencies_sample))
            compared_to_interval_median = float(np.median(compared_to_interval_latencies_sample))

            percentual_diff = (
                (comparison_interval_median - compared_to_interval_median)
                / compared_to_interval_median
                * 100
            )

            _, p, _, _ = median_test(
                comparison_interval_latencies_sample, compared_to_interval_latencies_sample
            )

            is_significant = abs(float(percentual_diff)) > 0 and float(p) < 0.05

            return MedianLatencyAnswer(
                is_significant=is_significant,
                percentual_diff=percentual_diff,
                # Sample latencies
                comparison_interval_latencies_sample=comparison_interval_latencies_sample,
                compared_to_interval_latencies_sample=compared_to_interval_latencies_sample,
                # Latency medians
                comparison_interval_median=comparison_interval_median,
                compared_to_interval_median=compared_to_interval_median,
            )
