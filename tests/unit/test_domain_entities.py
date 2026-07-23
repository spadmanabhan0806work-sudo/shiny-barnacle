import pytest

from src.domain.entities.annotation import Annotation, GroundTruth
from src.domain.entities.call_recording import CallRecording, CallStatus
from src.domain.entities.intent_extraction import IntentExtraction
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.trade_side import TradeSide


class TestGroundTruth:
    def test_valid_ground_truth(self):
        gt = GroundTruth(
            side="BUY",
            stock_symbol="RELIANCE",
            quantity=100,
            price=2500.50,
            exchange="NSE",
        )
        assert gt.side == "BUY"
        assert gt.quantity == 100

    def test_invalid_side_raises(self):
        with pytest.raises(ValueError, match="Invalid trade side"):
            GroundTruth(
                side="HOLD",
                stock_symbol="RELIANCE",
                quantity=100,
                price=2500.0,
                exchange="NSE",
            )

    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError, match="Quantity must be positive"):
            GroundTruth(
                side="BUY",
                stock_symbol="RELIANCE",
                quantity=0,
                price=2500.0,
                exchange="NSE",
            )

    def test_invalid_exchange_raises(self):
        with pytest.raises(ValueError, match="Invalid exchange"):
            GroundTruth(
                side="BUY",
                stock_symbol="RELIANCE",
                quantity=100,
                price=2500.0,
                exchange="NYSE",
            )


class TestCallRecording:
    def test_default_status_is_pending(self):
        call = CallRecording(tenant_id="default", storage_key="test/audio.wav")
        assert call.status == CallStatus.PENDING

    def test_mark_processing(self):
        call = CallRecording(tenant_id="default", storage_key="test/audio.wav")
        call.mark_processing()
        assert call.status == CallStatus.PROCESSING

    def test_mark_completed(self):
        call = CallRecording(tenant_id="default", storage_key="test/audio.wav")
        call.mark_completed()
        assert call.status == CallStatus.COMPLETED


class TestAnnotation:
    def test_submit_changes_status(self):
        gt = GroundTruth(
            side="SELL", stock_symbol="TCS", quantity=50, price=3500.0, exchange="NSE"
        )
        from uuid import uuid4

        annotation = Annotation(call_id=uuid4(), annotator_id="user1", ground_truth=gt)
        annotation.submit()
        from src.domain.entities.annotation import AnnotationStatus

        assert annotation.status == AnnotationStatus.SUBMITTED


class TestTradeSide:
    def test_from_string_buy(self):
        assert TradeSide.from_string("buy") == TradeSide.BUY

    def test_from_string_sell(self):
        assert TradeSide.from_string("SELL") == TradeSide.SELL

    def test_invalid_side_raises(self):
        with pytest.raises(ValueError):
            TradeSide.from_string("HOLD")


class TestConfidence:
    def test_valid_confidence(self):
        conf = Confidence(0.95)
        assert conf.is_high

    def test_low_confidence(self):
        conf = Confidence(0.5)
        assert conf.is_low

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            Confidence(1.5)


class TestIntentExtraction:
    def test_valid_extraction(self):
        from uuid import uuid4

        extraction = IntentExtraction(
            call_id=uuid4(),
            side="BUY",
            stock_symbol="RELIANCE",
            quantity=100,
            price=2500.0,
            exchange="NSE",
            confidence=0.92,
        )
        assert extraction.confidence == 0.92

    def test_invalid_confidence_raises(self):
        from uuid import uuid4

        with pytest.raises(ValueError, match="Confidence must be between"):
            IntentExtraction(
                call_id=uuid4(),
                side="BUY",
                stock_symbol="RELIANCE",
                quantity=100,
                price=2500.0,
                exchange="NSE",
                confidence=1.5,
            )
