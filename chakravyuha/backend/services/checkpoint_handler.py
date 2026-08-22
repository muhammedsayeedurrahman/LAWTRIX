"""Human checkpoint handling for automation.

Manages human intervention points in automation workflow with pause/resume capability.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from backend.models.automation_state import (
    AutomationSession,
    AutomationStateEnum,
    AutomationStateMachine,
    CheckpointType,
    HumanCheckpoint,
    StateTransitionReason,
)


class CheckpointResponse(BaseModel):
    """Response for checkpoint creation."""
    checkpoint_id: str
    checkpoint_type: CheckpointType
    title: str
    reason: str
    user_action_required: str
    what_happens_next: str
    can_resume: bool
    timeout_at: datetime | None = None


class CheckpointCompletionRequest(BaseModel):
    """Request to complete a checkpoint."""
    checkpoint_id: str
    user_id: str | None = None
    checkpoint_data: dict = Field(default_factory=dict, description="Data from checkpoint (OTP, etc.)")


class CheckpointHandler:
    """Handles human checkpoints in automation workflow."""

    # Checkpoint timeout durations (in minutes)
    CHECKPOINT_TIMEOUTS = {
        CheckpointType.LOGIN: 30,
        CheckpointType.OTP: 10,
        CheckpointType.CAPTCHA: 5,
        CheckpointType.PAYMENT: 60,
        CheckpointType.REVIEW: None,  # No timeout
        CheckpointType.CONFIRMATION: 30,
    }

    def __init__(self):
        pass

    async def create_login_checkpoint(
        self,
        session: AutomationSession,
        portal_name: str,
        login_url: str,
    ) -> tuple[AutomationSession, CheckpointResponse]:
        """Create LOGIN checkpoint.

        Args:
            session: Current automation session
            portal_name: Name of portal requiring login
            login_url: URL where user should log in

        Returns:
            (Updated session, Checkpoint response)
        """
        state_machine = AutomationStateMachine(session)

        # Transition to WAITING_FOR_LOGIN state
        session = state_machine.transition(
            to_state=AutomationStateEnum.WAITING_FOR_LOGIN,
            reason=StateTransitionReason.CHECKPOINT_REQUIRED,
            details=f"Login required for {portal_name}",
        )

        # Create checkpoint
        state_machine = AutomationStateMachine(session)
        session = state_machine.create_checkpoint(
            checkpoint_type=CheckpointType.LOGIN,
            title="Login Required",
            reason=f"{portal_name} requires you to log in with your credentials",
            user_action_required=(
                f"1. Open {portal_name} in your browser\\n"
                f"2. Navigate to: {login_url}\\n"
                f"3. Log in with your username and password\\n"
                f"4. Return here and click 'Continue' when logged in"
            ),
            what_happens_next="Automation will resume filling the form after login",
            resume_state=AutomationStateEnum.FILLING,
            data={"portal_name": portal_name, "login_url": login_url},
        )

        checkpoint = session.current_checkpoint
        timeout = self._calculate_timeout(CheckpointType.LOGIN)

        response = CheckpointResponse(
            checkpoint_id=checkpoint.checkpoint_id,
            checkpoint_type=checkpoint.checkpoint_type,
            title=checkpoint.title,
            reason=checkpoint.reason,
            user_action_required=checkpoint.user_action_required,
            what_happens_next=checkpoint.what_happens_next,
            can_resume=checkpoint.can_resume,
            timeout_at=timeout,
        )

        return session, response

    async def create_otp_checkpoint(
        self,
        session: AutomationSession,
        otp_sent_to: str,
        otp_length: int = 6,
    ) -> tuple[AutomationSession, CheckpointResponse]:
        """Create OTP checkpoint.

        Args:
            session: Current automation session
            otp_sent_to: Phone/email where OTP was sent
            otp_length: Expected OTP length

        Returns:
            (Updated session, Checkpoint response)
        """
        state_machine = AutomationStateMachine(session)

        session = state_machine.transition(
            to_state=AutomationStateEnum.WAITING_FOR_OTP,
            reason=StateTransitionReason.CHECKPOINT_REQUIRED,
            details=f"OTP sent to {otp_sent_to}",
        )

        state_machine = AutomationStateMachine(session)
        session = state_machine.create_checkpoint(
            checkpoint_type=CheckpointType.OTP,
            title="OTP Verification Required",
            reason=f"One-Time Password has been sent to {otp_sent_to}",
            user_action_required=(
                f"1. Check {otp_sent_to} for {otp_length}-digit OTP\\n"
                f"2. Enter OTP below\\n"
                f"3. Click 'Verify OTP'"
            ),
            what_happens_next="Automation will continue after OTP verification",
            resume_state=AutomationStateEnum.FILLING,
            data={
                "otp_sent_to": otp_sent_to,
                "otp_length": otp_length,
                "otp_field_selector": None,  # To be filled by browser automation
            },
        )

        checkpoint = session.current_checkpoint
        timeout = self._calculate_timeout(CheckpointType.OTP)

        response = CheckpointResponse(
            checkpoint_id=checkpoint.checkpoint_id,
            checkpoint_type=checkpoint.checkpoint_type,
            title=checkpoint.title,
            reason=checkpoint.reason,
            user_action_required=checkpoint.user_action_required,
            what_happens_next=checkpoint.what_happens_next,
            can_resume=checkpoint.can_resume,
            timeout_at=timeout,
        )

        return session, response

    async def create_captcha_checkpoint(
        self,
        session: AutomationSession,
        captcha_type: str = "image",
    ) -> tuple[AutomationSession, CheckpointResponse]:
        """Create CAPTCHA checkpoint.

        Args:
            session: Current automation session
            captcha_type: Type of CAPTCHA (image, audio, recaptcha)

        Returns:
            (Updated session, Checkpoint response)
        """
        state_machine = AutomationStateMachine(session)

        session = state_machine.transition(
            to_state=AutomationStateEnum.WAITING_FOR_CAPTCHA,
            reason=StateTransitionReason.CHECKPOINT_REQUIRED,
            details=f"CAPTCHA verification required ({captcha_type})",
        )

        state_machine = AutomationStateMachine(session)
        session = state_machine.create_checkpoint(
            checkpoint_type=CheckpointType.CAPTCHA,
            title="CAPTCHA Verification Required",
            reason="The portal requires CAPTCHA verification for security",
            user_action_required=(
                "1. View the CAPTCHA image/challenge\\n"
                "2. Solve the CAPTCHA\\n"
                "3. Enter the solution below\\n"
                "4. Click 'Verify'"
            ),
            what_happens_next="Automation will continue after CAPTCHA verification",
            resume_state=AutomationStateEnum.FILLING,
            data={"captcha_type": captcha_type},
        )

        checkpoint = session.current_checkpoint
        timeout = self._calculate_timeout(CheckpointType.CAPTCHA)

        response = CheckpointResponse(
            checkpoint_id=checkpoint.checkpoint_id,
            checkpoint_type=checkpoint.checkpoint_type,
            title=checkpoint.title,
            reason=checkpoint.reason,
            user_action_required=checkpoint.user_action_required,
            what_happens_next=checkpoint.what_happens_next,
            can_resume=checkpoint.can_resume,
            timeout_at=timeout,
        )

        return session, response

    async def create_payment_checkpoint(
        self,
        session: AutomationSession,
        amount: float,
        payment_method: str | None = None,
    ) -> tuple[AutomationSession, CheckpointResponse]:
        """Create PAYMENT checkpoint.

        Args:
            session: Current automation session
            amount: Payment amount
            payment_method: Payment method if known

        Returns:
            (Updated session, Checkpoint response)
        """
        state_machine = AutomationStateMachine(session)

        session = state_machine.transition(
            to_state=AutomationStateEnum.WAITING_FOR_PAYMENT,
            reason=StateTransitionReason.CHECKPOINT_REQUIRED,
            details=f"Payment required: Rs {amount}",
        )

        state_machine = AutomationStateMachine(session)
        payment_instructions = (
            f"1. Review payment amount: Rs {amount}\\n"
            f"2. Select payment method{' (' + payment_method + ')' if payment_method else ''}\\n"
            f"3. Complete payment on portal\\n"
            f"4. Wait for payment confirmation\\n"
            f"5. Return here and click 'Continue'"
        )

        session = state_machine.create_checkpoint(
            checkpoint_type=CheckpointType.PAYMENT,
            title="Payment Required",
            reason=f"Portal requires payment of Rs {amount}",
            user_action_required=payment_instructions,
            what_happens_next="Automation will continue after payment confirmation",
            resume_state=AutomationStateEnum.FILLING,
            data={"amount": amount, "payment_method": payment_method},
        )

        checkpoint = session.current_checkpoint
        timeout = self._calculate_timeout(CheckpointType.PAYMENT)

        response = CheckpointResponse(
            checkpoint_id=checkpoint.checkpoint_id,
            checkpoint_type=checkpoint.checkpoint_type,
            title=checkpoint.title,
            reason=checkpoint.reason,
            user_action_required=checkpoint.user_action_required,
            what_happens_next=checkpoint.what_happens_next,
            can_resume=checkpoint.can_resume,
            timeout_at=timeout,
        )

        return session, response

    async def create_review_checkpoint(
        self,
        session: AutomationSession,
        review_data: dict[str, Any],
    ) -> tuple[AutomationSession, CheckpointResponse]:
        """Create REVIEW checkpoint for user to review before submission.

        Args:
            session: Current automation session
            review_data: Data to be reviewed (form fields, documents, etc.)

        Returns:
            (Updated session, Checkpoint response)
        """
        state_machine = AutomationStateMachine(session)

        session = state_machine.transition(
            to_state=AutomationStateEnum.READY_FOR_USER_REVIEW,
            reason=StateTransitionReason.CHECKPOINT_REQUIRED,
            details="User review required before submission",
        )

        state_machine = AutomationStateMachine(session)
        session = state_machine.create_checkpoint(
            checkpoint_type=CheckpointType.REVIEW,
            title="Review Before Submission",
            reason="Please review all details before final submission",
            user_action_required=(
                "1. Review all filled information\\n"
                "2. Check attached documents\\n"
                "3. Verify all details are correct\\n"
                "4. Click 'Approve' to proceed or 'Edit' to make changes"
            ),
            what_happens_next="Final submission will proceed after approval",
            resume_state=AutomationStateEnum.USER_CONFIRMED,
            data=review_data,
        )

        checkpoint = session.current_checkpoint

        response = CheckpointResponse(
            checkpoint_id=checkpoint.checkpoint_id,
            checkpoint_type=checkpoint.checkpoint_type,
            title=checkpoint.title,
            reason=checkpoint.reason,
            user_action_required=checkpoint.user_action_required,
            what_happens_next=checkpoint.what_happens_next,
            can_resume=checkpoint.can_resume,
            timeout_at=None,  # No timeout for review
        )

        return session, response

    async def create_final_confirmation_checkpoint(
        self,
        session: AutomationSession,
        submission_summary: str,
    ) -> tuple[AutomationSession, CheckpointResponse]:
        """Create CONFIRMATION checkpoint for final irreversible submission.

        Args:
            session: Current automation session
            submission_summary: Summary of what will be submitted

        Returns:
            (Updated session, Checkpoint response)
        """
        state_machine = AutomationStateMachine(session)

        session = state_machine.transition(
            to_state=AutomationStateEnum.FINAL_CONFIRMATION_REQUIRED,
            reason=StateTransitionReason.CHECKPOINT_REQUIRED,
            details="Final confirmation required before irreversible submission",
        )

        state_machine = AutomationStateMachine(session)
        session = state_machine.create_checkpoint(
            checkpoint_type=CheckpointType.CONFIRMATION,
            title="Final Confirmation Required",
            reason="This is an irreversible action",
            user_action_required=(
                "IMPORTANT: This action cannot be undone\\n\\n"
                f"{submission_summary}\\n\\n"
                "Click 'Confirm and Submit' to proceed\\n"
                "Click 'Go Back' to review or cancel"
            ),
            what_happens_next="Your request will be submitted to the authority",
            resume_state=AutomationStateEnum.SUBMITTING,
            data={"submission_summary": submission_summary},
        )

        checkpoint = session.current_checkpoint
        timeout = self._calculate_timeout(CheckpointType.CONFIRMATION)

        response = CheckpointResponse(
            checkpoint_id=checkpoint.checkpoint_id,
            checkpoint_type=checkpoint.checkpoint_type,
            title=checkpoint.title,
            reason=checkpoint.reason,
            user_action_required=checkpoint.user_action_required,
            what_happens_next=checkpoint.what_happens_next,
            can_resume=checkpoint.can_resume,
            timeout_at=timeout,
        )

        return session, response

    async def complete_checkpoint(
        self,
        session: AutomationSession,
        request: CheckpointCompletionRequest,
    ) -> AutomationSession:
        """Complete a checkpoint and transition to next state.

        Args:
            session: Current automation session
            request: Checkpoint completion request with data

        Returns:
            Updated automation session

        Raises:
            ValueError: If no active checkpoint or checkpoint ID mismatch
        """
        if not session.current_checkpoint:
            raise ValueError("No active checkpoint")

        if session.current_checkpoint.checkpoint_id != request.checkpoint_id:
            raise ValueError(
                f"Checkpoint ID mismatch. Expected {session.current_checkpoint.checkpoint_id}, "
                f"got {request.checkpoint_id}"
            )

        state_machine = AutomationStateMachine(session)

        # Complete the checkpoint
        session = state_machine.complete_checkpoint()

        # Transition to resume state if specified
        if session.completed_checkpoints[-1].resume_state:
            resume_state = session.completed_checkpoints[-1].resume_state
            state_machine = AutomationStateMachine(session)
            session = state_machine.transition(
                to_state=resume_state,
                reason=StateTransitionReason.CHECKPOINT_COMPLETED,
                details=f"Checkpoint {request.checkpoint_id} completed",
                user_id=request.user_id,
            )

        return session

    async def cancel_checkpoint(
        self,
        session: AutomationSession,
        reason: str | None = None,
    ) -> AutomationSession:
        """Cancel current checkpoint and return to review state.

        Args:
            session: Current automation session
            reason: Reason for cancellation

        Returns:
            Updated automation session
        """
        if not session.current_checkpoint:
            raise ValueError("No active checkpoint to cancel")

        state_machine = AutomationStateMachine(session)

        # Complete checkpoint without transitioning
        session = state_machine.complete_checkpoint()

        # Go back to review state
        state_machine = AutomationStateMachine(session)
        session = state_machine.transition(
            to_state=AutomationStateEnum.READY_FOR_USER_REVIEW,
            reason=StateTransitionReason.USER_ACTION,
            details=f"Checkpoint cancelled: {reason or 'User cancelled'}",
        )

        return session

    def _calculate_timeout(self, checkpoint_type: CheckpointType) -> datetime | None:
        """Calculate timeout for checkpoint type.

        Args:
            checkpoint_type: Type of checkpoint

        Returns:
            Timeout datetime or None if no timeout
        """
        timeout_minutes = self.CHECKPOINT_TIMEOUTS.get(checkpoint_type)
        if timeout_minutes is None:
            return None

        return datetime.utcnow() + timedelta(minutes=timeout_minutes)

    def is_checkpoint_expired(self, checkpoint: HumanCheckpoint) -> bool:
        """Check if checkpoint has expired.

        Args:
            checkpoint: Checkpoint to check

        Returns:
            True if checkpoint has expired
        """
        timeout_minutes = self.CHECKPOINT_TIMEOUTS.get(checkpoint.checkpoint_type)
        if timeout_minutes is None:
            return False  # No timeout

        elapsed_minutes = (datetime.utcnow() - checkpoint.created_at).total_seconds() / 60
        return elapsed_minutes > timeout_minutes
