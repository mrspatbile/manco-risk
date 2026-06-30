"""PRIIPs Summary Risk Indicator (SRI) calculation engine.

Stateless, pure calculation. No I/O or persistence.
"""

from manco_risk.risk.priips.constants import CRM_DEFAULT_CLASS, SRI_COMBINATION_TABLE
from manco_risk.risk.priips.sri import SRIInput, SRIResult


class SRIEngine:
    """PRIIPs SRI calculation engine.

    Combines MRM and CRM classes into final SRI class using the regulatory
    combination table from Commission Delegated Regulation (EU) 2017/653
    Annex II.

    The engine is stateless. Calculation is deterministic: same input always
    produces the same output.

    Methodology:
    1. Normalize CRM: if None (not applicable), use CRM_DEFAULT_CLASS (1).
    2. Look up SRI class from SRI_COMBINATION_TABLE[crm_class][mrm_class].
    3. Return immutable SRIResult with normalized CRM and computed SRI.

    Reference:
    - Commission Delegated Regulation (EU) 2017/653, Annex II: MRM/CRM
      combination table for SRI determination.
    """

    @staticmethod
    def calculate(input_data: SRIInput) -> SRIResult:
        """Calculate SRI class from MRM and CRM classes.

        Parameters
        ----------
        input_data : SRIInput
            Input containing product_id, valuation_date, mrm_class, and
            optional crm_class.

        Returns
        -------
        SRIResult
            Immutable result with normalized crm_class and computed sri_class.

        Raises
        ------
        KeyError
            If MRM or CRM class not in the regulatory table (should not occur
            if input validation is correct).
        """
        # Normalize CRM: None → default class 1 (neutral credit risk)
        crm_normalized = (
            input_data.crm_class if input_data.crm_class is not None else CRM_DEFAULT_CLASS
        )

        # Look up SRI class from regulatory combination table
        sri_class = SRI_COMBINATION_TABLE[crm_normalized][input_data.mrm_class]

        # Return immutable result
        return SRIResult(
            product_id=input_data.product_id,
            valuation_date=input_data.valuation_date,
            mrm_class=input_data.mrm_class,
            crm_class=crm_normalized,
            sri_class=sri_class,
        )
