import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta
try:
    from .file_reader import FileReader
except Exception:
    from file_reader import FileReader
import uuid
import pytz
import streamlit as st

# Scenario rules for SPO status update
SPO_STATUS_UPDATE_SCENARIOS = [
    # 1) Encoded -> Commissioned
    {"current_state": "ENCODED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Available", "reason": "Not Applicable", "actions": ["ADD"], "bizsteps": ["commissioning"], "dispositions": ["active"]},
    {"current_state": "ENCODED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Picked", "reason": "Not Applicable", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "picking"], "dispositions": ["active", "in_progress"]},
    {"current_state": "ENCODED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Damaged", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "damaged"]},
    {"current_state": "ENCODED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Expired", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "expired"]},
    {"current_state": "ENCODED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Misplaced", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "unknown"]},
    {"current_state": "ENCODED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Recalled", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "recalled"]},
    {"current_state": "ENCODED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Stolen", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "stolen"]},
    {"current_state": "ENCODED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Blocked", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "non_sellable_other"]},
    {"current_state": "ENCODED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Under Investigation", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "non_sellable_other"]},
    {"current_state": "ENCODED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Withdrawn", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "non_sellable_other"]},

    # 2) Commissioned -> Destroyed
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "None", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "Damaged", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["damaged"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "Disposed", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["disposed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "Expired", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["expired"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "Illegitimate", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "Misplaced", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["unknown"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "Recalled", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["recalled"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "Sampled", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "Other", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "UAE - Improper Storage", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "UAE - Exceeded Environment Conditions", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "UAE - Contaminated", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "UZ - Defect", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "UZ - QA Samples", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "UZ - Complaints", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "UZ - Product Testing", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "UZ - Demo Samples", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "KZ - Defect", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "KZ - QA Samples", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "KZ - Compliants", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "KZ - Product Testing", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},
    {"current_state": "COMMISSIONED", "target_state": "DESTROYED", "current_logistic": None, "target_logistic": None, "reason": "KZ - Demo Samples", "actions": ["DELETE"], "bizsteps": ["destroying"], "dispositions": ["destroyed"]},

    # 3) Commissioned -> Decommissioned
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "Disposed", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["disposed"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "Illegitimate", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "Damaged", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["damaged"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "Expired", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["expired"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "Misplaced", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["unknown"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "Recalled", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["recalled"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "Stolen", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["stolen"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "Withdrawn Sampled", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "Sampled by Authorities", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "Other", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "UAE - Broken", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "UAE - Unfolded", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "UAE - Torn", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "UAE - 2D Matrix not readable", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "UAE - Smashed", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "UAE - Damage due to liquid spill", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "UZ - Defect", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "UZ - QA Samples", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "UZ - Complaints", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "UZ - Product Testing", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "UZ - Demo Samples", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "KZ - Defect", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "KZ - QA Samples", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "KZ - Compliants", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "KZ - Product Testing", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "KZ - Demo Samples", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},
    {"current_state": "COMMISSIONED", "target_state": "DECOMMISSIONED", "current_logistic": None, "target_logistic": None, "reason": "EU - Checked Out", "actions": ["DELETE"], "bizsteps": ["decommissioning"], "dispositions": ["inactive"]},

    # 4) Commissioned -> Commissioned
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Available", "target_logistic": "Picked", "reason": "Not Applicable", "actions": ["OBSERVE"], "bizsteps": ["picking"], "dispositions": ["in_progress"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Available", "target_logistic": "Holding", "reason": "Damaged", "actions": ["OBSERVE"], "bizsteps": ["holding"], "dispositions": ["damaged"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Available", "target_logistic": "Holding", "reason": "Expired", "actions": ["OBSERVE"], "bizsteps": ["holding"], "dispositions": ["expired"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Available", "target_logistic": "Holding", "reason": "Misplaced", "actions": ["OBSERVE"], "bizsteps": ["holding"], "dispositions": ["unknown"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Available", "target_logistic": "Holding", "reason": "Recalled", "actions": ["OBSERVE"], "bizsteps": ["holding"], "dispositions": ["recalled"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Available", "target_logistic": "Holding", "reason": "Stolen", "actions": ["OBSERVE"], "bizsteps": ["holding"], "dispositions": ["stolen"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Available", "target_logistic": "Holding", "reason": "Blocked", "actions": ["OBSERVE"], "bizsteps": ["holding"], "dispositions": ["non_sellable_other"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Available", "target_logistic": "Holding", "reason": "Under Investigation", "actions": ["OBSERVE"], "bizsteps": ["holding"], "dispositions": ["non_sellable_other"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Available", "target_logistic": "Holding", "reason": "Withdrawn", "actions": ["OBSERVE"], "bizsteps": ["holding"], "dispositions": ["non_sellable_other"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Available", "target_logistic": "Pending Receipt", "reason": "Not Applicable", "actions": ["OBSERVE"], "bizsteps": ["transporting"], "dispositions": ["in_progress"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Pending Receipt", "target_logistic": "Available", "reason": "Not Applicable", "actions": ["OBSERVE"], "bizsteps": ["omit"], "dispositions": ["omit"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Shipped", "target_logistic": "Received", "reason": "Not Applicable", "actions": ["OBSERVE"], "bizsteps": ["omit"], "dispositions": ["omit"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Received", "target_logistic": "Shipped", "reason": "Not Applicable", "actions": ["OBSERVE"], "bizsteps": ["transporting"], "dispositions": ["in_progress"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Picked", "target_logistic": "Available", "reason": "Not Applicable", "actions": ["OBSERVE"], "bizsteps": ["void_picking"], "dispositions": ["in_progress"]},
    {"current_state": "COMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": "Holding", "target_logistic": "Available", "reason": "Not Applicable", "actions": ["OBSERVE"], "bizsteps": ["stocking"], "dispositions": ["sellable_accessible"]},

    # 5) Decommissioned -> Commissioned
    {"current_state": "DECOMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Available", "reason": "Not Applicable", "actions": ["ADD"], "bizsteps": ["commissioning"], "dispositions": ["active"]},
    {"current_state": "DECOMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Picked", "reason": "Not Applicable", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "picking"], "dispositions": ["active", "in_progress"]},
    {"current_state": "DECOMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Damaged", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "damaged"]},
    {"current_state": "DECOMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Expired", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "expired"]},
    {"current_state": "DECOMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Misplaced", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "unknown"]},
    {"current_state": "DECOMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Recalled", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "recalled"]},
    {"current_state": "DECOMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Stolen", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "stolen"]},
    {"current_state": "DECOMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Blocked", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "non_sellable_other"]},
    {"current_state": "DECOMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Under Investigation", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "non_sellable_other"]},
    {"current_state": "DECOMMISSIONED", "target_state": "COMMISSIONED", "current_logistic": None, "target_logistic": "Holding", "reason": "Withdrawn", "actions": ["ADD", "OBSERVE"], "bizsteps": ["commissioning", "holding"], "dispositions": ["active", "non_sellable_other"]},
]



get_update_tags = {
    ("DECOMMISSIONED", "Dispensed"): ("decommissioning", "dispensed"),
    ("DECOMMISSIONED", "Damaged"): ("decommissioning", "damaged"),
    ("DECOMMISSIONED", "Disposed"): ("decommissioning", "disposed"),
    ("DECOMMISSIONED", "Expired"): ("decommissioning", "expired"),
    ("DECOMMISSIONED", "Illegitimate"): ("decommissioning", "inactive"),
    ("DECOMMISSIONED", "Misplaced"): ("decommissioning", "unknown"),
    ("DECOMMISSIONED", "Recalled"): ("decommissioning", "recalled"),
    ("DECOMMISSIONED", "Stolen"): ("decommissioning", "stolen"),
    ("DECOMMISSIONED", "Quality Released"): ("decommissioning", "inactive"),
    ("DECOMMISSIONED", "Repackaged"): ("decommissioning", "inactive"),
    ("DECOMMISSIONED", "Withdrawn/Sampled"): ("decommissioning", "inactive"),
    ("DECOMMISSIONED", "Sampled by Authorities"): ("decommissioning", "inactive"),
    ("DESTROYED", "Damaged"): ("destroying", "damaged"),
    ("DESTROYED", "Destroyed"): ("destroying", "destroyed"),
    ("DESTROYED", "Disposed"): ("destroying", "disposed"),
    ("DESTROYED", "Expired"): ("destroying", "expired"),
    ("DESTROYED", "Illegitimate"): ("destroying", "destroyed"),
    ("DESTROYED", "Misplaced"): ("destroying", "unknown"),
    ("DESTROYED", "Recalled"): ("destroying", "recalled"),
    ("DESTROYED", "Stolen"): ("destroying", "stolen"),
    ("DESTROYED", "Sampled"): ("destroying", "destroyed")
}

get_delivery_tags = {
    ("OUTBOUND", "DRAFT", "Sale Export"): ("picking", "in_progress"),
    ("OUTBOUND", "DRAFT", "Sale in Country"): ("picking", "in_progress"),
    ("OUTBOUND", "DRAFT", "Return Export"): ("picking", "in_progress"),
    ("OUTBOUND", "DRAFT", "Return in Country"): ("picking", "in_progress"),
    ("OUTBOUND", "DRAFT", "Transfer Export"): ("picking", "in_progress"),
    ("OUTBOUND", "DRAFT", "Transfer in Country"): ("picking", "in_progress"),
    ("OUTBOUND", "SUBMITTED", "Sale Export"): ("shipping", "in_transit"),
    ("OUTBOUND", "SUBMITTED", "Sale in Country"): ("shipping", "in_transit"),
    ("OUTBOUND", "SUBMITTED", "Return Export"): ("shipping", "returned"),
    ("OUTBOUND", "SUBMITTED", "Return in Country"): ("shipping", "returned"),
    ("OUTBOUND", "SUBMITTED", "Transfer Export"): ("shipping", "in_transit"),
    ("OUTBOUND", "SUBMITTED", "Transfer in Country"): ("shipping", "in_transit"),
    ("OUTBOUND", "VOIDED", "Sale Export"): ("void_picking", "in_progress"),
    ("OUTBOUND", "VOIDED", "Sale in Country"): ("void_picking", "in_progress"),
    ("OUTBOUND", "VOIDED", "Return Export"): ("void_picking", "in_progress"),
    ("OUTBOUND", "VOIDED", "Return in Country"): ("void_picking", "in_progress"),
    ("OUTBOUND", "VOIDED", "Transfer Export"): ("void_picking", "in_progress"),
    ("OUTBOUND", "VOIDED", "Transfer in Country"): ("void_picking", "in_progress"),
    ("OUTBOUND", "CANCELLED", "Sale Export"): ("void_shipping", "in_progress"),
    ("OUTBOUND", "CANCELLED", "Sale in Country"): ("void_shipping", "in_progress"),
    ("OUTBOUND", "CANCELLED", "Return Export"): ("void_shipping", "in_progress"),
    ("OUTBOUND", "CANCELLED", "Return in Country"): ("void_shipping", "in_progress"),
    ("OUTBOUND", "CANCELLED", "Transfer Export"): ("void_shipping", "in_progress"),
    ("OUTBOUND", "CANCELLED", "Transfer in Country"): ("void_shipping", "in_progress"),
    ("INBOUND", "DRAFT", "Return Import"): ("pending_receipt", "in_progress"),
    ("INBOUND", "DRAFT", "Return in Country"): ("pending_receipt", "in_progress"),
    ("INBOUND", "DRAFT", "Purchase Import"): ("pending_receipt", "in_progress"),
    ("INBOUND", "DRAFT", "Purchase in Country"): ("pending_receipt", "in_progress"),
    ("INBOUND", "DRAFT", "Transfer Import"): ("pending_receipt", "in_progress"),
    ("INBOUND", "DRAFT", "Transfer in Country"): ("pending_receipt", "in_progress"),
    ("INBOUND", "SUBMITTED", "Return Import"): ("receiving", "returned"),
    ("INBOUND", "SUBMITTED", "Return in Country"): ("receiving", "returned"),
    ("INBOUND", "SUBMITTED", "Purchase Import"): ("receiving", "active"),
    ("INBOUND", "SUBMITTED", "Purchase in Country"): ("receiving", "active"),
    ("INBOUND", "SUBMITTED", "Transfer Import"): ("receiving", "active"),
    ("INBOUND", "SUBMITTED", "Transfer in Country"): ("receiving", "active"),
    ("INBOUND", "VOIDED", "Return Import"): ("void_receiving", "in_progress"),
    ("INBOUND", "VOIDED", "Return in Country"): ("void_receiving", "in_progress"),
    ("INBOUND", "VOIDED", "Purchase Import"): ("void_receiving", "in_progress"),
    ("INBOUND", "VOIDED", "Purchase in Country"): ("void_receiving", "in_progress"),
    ("INBOUND", "VOIDED", "Transfer Import"): ("void_receiving", "in_progress"),
    ("INBOUND", "VOIDED", "Transfer in Country"): ("void_receiving", "in_progress"),
    ("INBOUND", "CANCELLED", "Return Import"): ("void_receiving", "in_progress"),
    ("INBOUND", "CANCELLED", "Return in Country"): ("void_receiving", "in_progress"),
    ("INBOUND", "CANCELLED", "Purchase Import"): ("void_receiving", "in_progress"),
    ("INBOUND", "CANCELLED", "Purchase in Country"): ("void_receiving", "in_progress"),
    ("INBOUND", "CANCELLED", "Transfer Import"): ("void_receiving", "in_progress"),
    ("INBOUND", "CANCELLED", "Transfer in Country"): ("void_receiving", "in_progress"),
    # ("default_delivery_type", "SUBMITTED"): ("shipping", "in_transit")
}

transaction_identifiers_tags = {
    "Bill of Lading": "BILL_OF_LADING",
    "Destruction Order": "DESTRUCTION_ORDER",
    "E-Way Bill Number": "E_WAY_BILL_NUMBER",
    "Import Permit": "IMPORT_PERMIT",
    "Invoice Number": "INVOICE_NUMBER",
    "Nota Fiscal Electronica": "NOTA_FISCAL_ELECTRONICA",
    "Packing Slip Number": "PACKING_SLIP_NUMBER",
    "Purchase Order": "PURCHASE_ORDER",
    "PRO Number": "PRO_NUMBER",
    "Return": "RETURN",
    "Sales Order Number": "SALES_ORDER_NUMBER",
    "Sales Permit": "SALES_PERMIT",
    "Shipment Number": "SHIPMENT_NUMBER",
    "Shipment Permit": "SHIPMENT_PERMIT",
    "Local Sales Permit": "LOCAL_SALES_PERMIT",
    "Transfer Number": "TRANSFER_NUMBER",
    "Other": "OTHER",
}

"""
Transaction identifier tags where keys are transaction identifier names and values are corresponding tags
"""
get_identifier_tag = {
    "Bill of Lading": "bol",
    "Destruction Order": "destruction",
    "E-Way Bill Number": "eway",
    "Import Permit": "importpermit",
    "Invoice Number": "inv",
    "Nota Fiscal Electronica": "notafiscaleletronica",
    "Packing Slip Number": "packslip",
    "Purchase Order": "po",
    "PRO Number": "prodorder",
    "Return": "rma",
    "Sales Order Number": "salesorder",
    "Sales Permit": "salespermit",
    "Shipment Number": "shipment",
    "Shipment Permit": "shipmentpermit",
    "Local Sales Permit": "localsalespermit",
    "Transfer Number": "transfer",
    "Other": "other",    
}


class EPICSGenerator:

    def __init__(self, data):
        """
        Initialize the EPICSGenerator with provided data.

        This constructor sets up the namespace mappings, initializes the input data,
        and prepares containers for processed data and event timing information.

        Args:
            data (dict): The input data for generating EPCIS information.
        """

        self.ns = {
            "epcis": "urn:epcglobal:epcis:xsd:1",
            "cbvmd": "urn:epcglobal:cbv:mda",
            "ah": "https://www.altiushub.com/epcis/namespace/AltiushubExtension",
        }
        self.data = data
        self.processed_data = []
        self.event_timing = None
        # Convert serial numbers to URNs for all modules
        self._convert_serials_to_urns()

    def _convert_serials_to_urns(self):
        """
        Convert serial numbers to URNs for all modules that have file data.
        This ensures URNs are available for event generation.
        """
        try:
            import os
            
            modules = self.data.get('modules', {})
            gcp = self.data.get('gcp', '')
            
            if not gcp:
                print("Warning: No GCP provided for URN conversion")
                return
            
            # Process SNI data
            if 'SNI' in modules:
                sni_data = modules['SNI']
                print(f"Processing SNI data: {sni_data.keys()}")
                
                # Process commissioning levels
                if 'commissioning' in sni_data:
                    print(f"Found commissioning levels: {list(sni_data['commissioning'].keys())}")
                    for level, level_data in sni_data['commissioning'].items():
                        if isinstance(level_data, dict) and 'file_path' in level_data and 'urns' not in level_data:
                            file_path = level_data['file_path']
                            print(f"Processing {level} level file: {file_path}")
                            if file_path and isinstance(file_path, str) and os.path.exists(file_path):
                                freader_obj = FileReader(file_path, gcp)
                                df = freader_obj._read_file()
                                if "Serial Numbers" in df.columns:
                                    serials = df["Serial Numbers"].dropna().astype(str).tolist()
                                    urns = freader_obj.serial_number_to_urn(serials)
                                    level_data['urns'] = urns
                                    print(f"Converted {len(urns)} serials to URNs for {level} level")
                                else:
                                    print(f"No 'Serial Numbers' column found in {file_path}")
                            else:
                                print(f"File not found: {file_path}")
                
                # Process update data
                if 'update' in sni_data and isinstance(sni_data['update'], dict):
                    update_data = sni_data['update']
                    if 'file_path' in update_data and 'urns' not in update_data:
                        file_path = update_data['file_path']
                        print(f"Processing update file: {file_path}")
                        if file_path and isinstance(file_path, str) and os.path.exists(file_path):
                            freader_obj = FileReader(file_path, gcp)
                            df = freader_obj._read_file()
                            if "Serial Numbers" in df.columns:
                                serials = df["Serial Numbers"].dropna().astype(str).tolist()
                                urns = freader_obj.serial_number_to_urn(serials)
                                update_data['urns'] = urns
                                print(f"Converted {len(urns)} serials to URNs for update")
                            else:
                                print(f"No 'Serial Numbers' column found in update file: {file_path}")
                        else:
                            print(f"Update file not found: {file_path}")

                # Process disaggregation data
                if 'disaggregation' in sni_data and isinstance(sni_data['disaggregation'], list):
                    print(f"Found {len(sni_data['disaggregation'])} disaggregation mappings")
                    for idx, disagg_mapping in enumerate(sni_data['disaggregation']):
                        if isinstance(disagg_mapping, dict):
                            # Process parent file
                            if 'parent_file' in disagg_mapping and isinstance(disagg_mapping['parent_file'], dict):
                                parent_file = disagg_mapping['parent_file']
                                if 'file_path' in parent_file and 'urns' not in parent_file:
                                    file_path = parent_file['file_path']
                                    print(f"Processing disaggregation parent file {idx+1}: {file_path}")
                                    if file_path and isinstance(file_path, str) and os.path.exists(file_path):
                                        freader_obj = FileReader(file_path, gcp)
                                        df = freader_obj._read_file()
                                        if "Serial Numbers" in df.columns:
                                            serials = df["Serial Numbers"].dropna().astype(str).tolist()
                                            urns = freader_obj.serial_number_to_urn(serials)
                                            parent_file['urns'] = urns
                                            print(f"Converted {len(urns)} parent serials to URNs for disaggregation {idx+1}")
                                        else:
                                            print(f"No 'Serial Numbers' column found in parent file: {file_path}")
                                    else:
                                        print(f"Parent file not found: {file_path}")
                            
                            # Process child file
                            if 'child_file' in disagg_mapping and isinstance(disagg_mapping['child_file'], dict):
                                child_file = disagg_mapping['child_file']
                                if 'file_path' in child_file and 'urns' not in child_file:
                                    file_path = child_file['file_path']
                                    print(f"Processing disaggregation child file {idx+1}: {file_path}")
                                    if file_path and isinstance(file_path, str) and os.path.exists(file_path):
                                        freader_obj = FileReader(file_path, gcp)
                                        df = freader_obj._read_file()
                                        if "Serial Numbers" in df.columns:
                                            serials = df["Serial Numbers"].dropna().astype(str).tolist()
                                            urns = freader_obj.serial_number_to_urn(serials)
                                            child_file['urns'] = urns
                                            print(f"Converted {len(urns)} child serials to URNs for disaggregation {idx+1}")
                                        else:
                                            print(f"No 'Serial Numbers' column found in child file: {file_path}")
                                    else:
                                        print(f"Child file not found: {file_path}")

            # Process SPO data
            if 'SPO' in modules:
                spo_data = modules['SPO']
                
                # Process each SPO operation
                for operation in ['decommissioning', 'destruction', 'sampling']:
                    if operation in spo_data and isinstance(spo_data[operation], dict):
                        op_data = spo_data[operation]
                        if 'file_path' in op_data and 'urns' not in op_data:
                            file_path = op_data['file_path']
                            if file_path and isinstance(file_path, str) and os.path.exists(file_path):
                                freader_obj = FileReader(file_path, gcp)
                                df = freader_obj._read_file()
                                if "Serial Numbers" in df.columns:
                                    serials = df["Serial Numbers"].dropna().astype(str).tolist()
                                    urns = freader_obj.serial_number_to_urn(serials)
                                    op_data['urns'] = urns
                
                # Process status update scenarios
                if 'status_update' in spo_data and 'scenarios' in spo_data['status_update']:
                    for scenario in spo_data['status_update']['scenarios']:
                        if isinstance(scenario, dict) and 'file_path' in scenario and (
                            'urns' not in scenario or not scenario.get('urns')
                        ):
                            file_path = scenario['file_path']
                            if file_path and isinstance(file_path, str) and os.path.exists(file_path):
                                freader_obj = FileReader(file_path, gcp)
                                df = freader_obj._read_file()
                                if "Serial Numbers" in df.columns:
                                    serials = df["Serial Numbers"].dropna().astype(str).tolist()
                                    urns = freader_obj.serial_number_to_urn(serials)
                                    scenario['urns'] = urns
                                    print(f"Converted {len(urns)} serials to URNs for SPO status update scenario")
                                else:
                                    print(f"No 'Serial Numbers' column found in SPO status update scenario file: {file_path}")
                            else:
                                print(f"SPO status update scenario file not found: {file_path}")

            # Process WHD data
            if 'WHD' in modules:
                whd_data = modules['WHD']
                
                for operation in ['inbound', 'outbound']:
                    if operation in whd_data and isinstance(whd_data[operation], dict):
                        op_data = whd_data[operation]
                        if 'file' in op_data and isinstance(op_data['file'], dict) and 'file_path' in op_data['file'] and 'urns' not in op_data['file']:
                            file_path = op_data['file']['file_path']
                            print(f"Processing WHD {operation} file: {file_path}")
                            if file_path and isinstance(file_path, str) and os.path.exists(file_path):
                                freader_obj = FileReader(file_path, gcp)
                                df = freader_obj._read_file()
                                if "Serial Numbers" in df.columns:
                                    serials = df["Serial Numbers"].dropna().astype(str).tolist()
                                    urns = freader_obj.serial_number_to_urn(serials)
                                    op_data['urns'] = urns
                                    print(f"Converted {len(urns)} serials to URNs for WHD {operation}")
                                else:
                                    print(f"No 'Serial Numbers' column found in WHD {operation} file: {file_path}")
                            else:
                                print(f"WHD {operation} file not found: {file_path}")
        
        except Exception as e:
            print(f"Error: Could not convert serial numbers to URNs: {str(e)}")
            import traceback
            traceback.print_exc()

    def offset(self):
        """
        Get the timezone offset for the current time in Calcutta timezone.

        Returns:
            str: The timezone offset in the format +HH:MM or -HH:MM
        """
        dt = datetime.now()
        tz = pytz.timezone("Asia/Calcutta")
        offset_seconds = tz.utcoffset(dt).seconds
        # Handle offset better, ensuring two digits for hours and minutes
        hours_offset = offset_seconds // 3600
        minutes_offset = (offset_seconds % 3600) // 60
        return f"{hours_offset:+03}:{minutes_offset:02}"

    def generate_epcis_header(self):
        # Create StandardBusinessDocumentHeader with 'sbdh' prefix
        """
        Generate EPCIS header based on the input data.

        This function creates the EPCIS header based on the input data. The header
        includes information such as sender and receiver details, document
        identification, and creation date and time.

        :return: The EPCIS header element.
        :rtype: xml.etree.ElementTree.Element
        """
        header = ET.Element("EPCISHeader")
        ET.SubElement(
            header,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}StandardBusinessDocumentHeader",
        )

        # Create sub-elements with proper structure
        ET.SubElement(
            header,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}HeaderVersion",
        ).text = "1.0"

        # Sender information
        sender = ET.SubElement(
            header,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}Sender",
        )
        sender_gln = self.data.get("sender_gln")
        sender_authority = "GLN" if sender_gln else "SGLN"
        sender_id = ET.SubElement(
            sender,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}Identifier",
            {"Authority": f"{sender_authority}"},
        )
        if sender_gln:
            sender_id.text = (
                f"urn:epc:id:gln:{sender_gln}"
            )
        else:
            sender_id.text = (
                f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sender_sgln')}"
            )

        # Receiver information (fixing receiver id)
        receiver = ET.SubElement(
            header,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}Receiver",
        )
        receiver_gln = self.data.get("receiver_gln")
        receiver_authority = "GLN" if receiver_gln else "SGLN"
        receiver_id = ET.SubElement(
            receiver,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}Identifier",
            {"Authority": f"{receiver_authority}"},
        )
        if receiver_gln:
            receiver_id.text = (
                f"urn:epc:id:gln:{receiver_gln}"
            )
        else:
            receiver_id.text = (
                f"urn:epc:id:sgln:{self.data.get('receiver_sgln', 'default_receiver_sgln')}"
            )

        # Document Identification
        doc_id = ET.SubElement(
            header,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}DocumentIdentification",
        )
        ET.SubElement(
            doc_id,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}Standard",
        ).text = "EPCglobal"
        ET.SubElement(
            doc_id,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}TypeVersion",
        ).text = "1.0"
        ET.SubElement(
            doc_id,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}InstanceIdentifier",
        ).text = str(uuid.uuid4())
        ET.SubElement(
            doc_id,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}Type",
        ).text = "Events"
        ET.SubElement(
            doc_id,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}CreationDateAndTime",
        ).text = (
            datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )

        return header
    
    def generate_epcis_document(self):
        # Register namespaces
        ET.register_namespace("ah", self.ns["ah"])
        ET.register_namespace("cbvmd", self.ns["cbvmd"])
        ET.register_namespace("epcis", self.ns["epcis"])
        ET.register_namespace(
            "sbdh",
            "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader",
        )

        root = ET.Element(
            "{urn:epcglobal:epcis:xsd:1}EPCISDocument",
            attrib={
                "xmlns:ah": self.ns["ah"],
                "xmlns:cbvmd": self.ns["cbvmd"],
                # "xmlns:epcis": self.ns["epcis"],
                # "xmlns:sbdh": "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader",
                "schemaVersion": "1.2",
                "creationDate": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                + "Z",
            },
        )
        print(self.data)
        header_root = self.generate_epcis_header()
        print("done header root")
        body_root = self.generate_epcis_body()

        root.append(header_root)
        root.append(body_root)

        return root

    def create_element(self, parent, tag, text=None):
        element = ET.SubElement(parent, tag)
        if text:
            element.text = str(text).strip()
        return element

    def generate_object_event(
        self, object_type, eventtime, recordtime, main_root, serial_numbers, UOM_type
    ):
        """
        Generate an object event.

        This function generates an EPCIS object event using the provided data. It sets
        the event time, record time, action, bizstep, and disposition. It also includes
        a list of EPCs and sets the ReadPoint and BizLocation to the sender's SGLN.
        Conditional extensions are added based on the object type, which may include
        additional ilmd tags and custom fields.

        Args:
            object_type (str): The type of the object, used to determine conditional extensions.
            eventtime (str): The event time in the format "YYYY-MM-DDTHH:MM:SSZ".
            recordtime (str): The record time in the format "YYYY-MM-DDTHH:MM:SSZ".
            main_root (Element): The main root of the XML tree to which the event is attached.
            serial_numbers (list): A list of serial numbers for the EPCs.
            UOM_type (str): The unit of measure type, used in the extensions.

        Returns:
            Element: The generated object event.
        """
        root = ET.Element("ObjectEvent")

        # Basic event fields
        self.create_element(root, "eventTime", eventtime)
        self.create_element(root, "recordTime", recordtime)
        self.create_element(
            root, "eventTimeZoneOffset", self.offset()
        )  # Assuming a fixed offset for example

        # EPC list (serial numbers)
        epc_list = self.create_element(root, "epcList")
        for number in serial_numbers:
            self.create_element(epc_list, "epc", number)

        # Action, bizStep, and disposition
        self.create_element(root, "action", "ADD")
        self.create_element(root, "bizStep", "urn:epcglobal:cbv:bizstep:commissioning")
        self.create_element(root, "disposition", "urn:epcglobal:cbv:disp:active")

        # ReadPoint and BizLocation
        read_point = self.create_element(root, "readPoint")
        self.create_element(
            read_point,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}",
        )

        biz_location = self.create_element(root, "bizLocation")
        self.create_element(
            biz_location,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}",
        )

        # Conditional extensions based on object_type
        if (
            object_type == "01"
        ):  # Assuming "01" refers to a type that requires extensions
            extension = self.create_element(root, "extension")
            ilmd = self.create_element(extension, "ilmd")

            # Add specific custom fields within <ilmd>
            self.create_element(
                ilmd,
                "cbvmd:lotNumber",
                self.data.get("lot_number", "default_lot_number"),
            )
            self.create_element(
                ilmd,
                "cbvmd:manufacturingDate",
                self.data.get("manufacturing_date", "default_manufacturing_date"),
            )
            self.create_element(
                ilmd,
                "cbvmd:itemExpirationDate",
                self.data.get("expiration_date", "default_item_expiration_date"),
            )
            # self.create_element(ilmd, "cbvmd:manufacturingDate", self.data.get('manufacturing_date', 'default_manufacturing_date'))
            self.create_element(
                ilmd,
                "ah:internalMaterialCode",
                self.data.get(
                    "internal_material_code", "default_internal_material_code"
                ),
            )
            if UOM_type is not None:
                self.create_element(ilmd, "ah:packagingUom", UOM_type)
            # self.create_element(ilmd, "ah:countryDrugCodeValue", "00000-000-23")
            # self.create_element(ilmd, "ah:countryDrugCode", "US - NDC532")
            # self.create_element(ilmd, "ah:countryMarketCode", "US")
        else:
            extension = self.create_element(root, "extension")
            ilmd = self.create_element(extension, "ilmd")
            self.create_element(
                ilmd,
                "cbvmd:lotNumber",
                self.data.get("lot_number", "default_lot_number"),
            )
            self.create_element(
                ilmd,
                "cbvmd:manufacturingDate",
                self.data.get("manufacturing_date", "default_manufacturing_date"),
            )
            self.create_element(
                ilmd,
                "cbvmd:itemExpirationDate",
                self.data.get("expiration_date", "default_item_expiration_date"),
            )
            # Add extension digit for inner, case, and pallet UOM types
            if UOM_type in ["BU", "CA", "PA"]:
                # Extract extension digit from the first serial number (for SSCC URNs)
                extension_digit = None
                if serial_numbers and len(serial_numbers) > 0:
                    first_serial = serial_numbers[0]
                    # Check if it's an SSCC URN format (starts with 00)
                    if first_serial.startswith("urn:epc:id:sscc:"):
                        # Extract from URN: urn:epc:id:sscc:gcp.extensionDigit...
                        urn_parts = first_serial.split(":")
                        if len(urn_parts) >= 5:
                            gcp_extension = urn_parts[4].split(".")
                            if len(gcp_extension) >= 2:
                                extension_digit = gcp_extension[1][0]  # First character after GCP
                    else:
                        # Extract from raw serial number (position 2 for SSCC format)
                        # This handles cases where serial_numbers contains raw numbers
                        for number in serial_numbers:
                            if isinstance(number, str) and len(number) > 2 and not number.startswith("urn:"):
                                if number[:2] == "00":  # SSCC format
                                    extension_digit = number[2]
                                    break
                
                # Fallback to basic information if not found in serial numbers
                if extension_digit is None:
                    extension_digit = self.data.get("extension_digit", "0")
                
                self.create_element(
                    ilmd,
                    "ah:extensionDigit",
                    extension_digit,
                )
            self.create_element(
                ilmd,
                "ah:internalMaterialCode",
                self.data.get(
                    "internal_material_code", "default_internal_material_code"
                ),
            )
            self.create_element(ilmd, "ah:packagingUom", UOM_type)
        # Attach to the main root if provided
        if main_root is not None:
            main_root.append(root)

        return root

    def generate_aggregation_event(
        self, parentid, eventtime, recordtime, main_root, serial_numbers
    ):
        """
        Generate an aggregation event.

        This function generates an EPCIS aggregation event using the provided data.
        It sets the event time, record time, action, bizstep, and disposition.
        It also includes the parent ID and a list of child EPCs, and sets the 
        ReadPoint and BizLocation to the sender's SGLN.

        Args:
            parentid (str): The parent ID of the aggregation event.
            eventtime (str): The event time in the format "YYYY-MM-DDTHH:MM:SSZ".
            recordtime (str): The record time in the format "YYYY-MM-DDTHH:MM:SSZ".
            main_root (Element): The main root of the XML tree.
            serial_numbers (list): A list of serial numbers for child EPCs.

        Returns:
            Element: The generated aggregation event.
        """
        root = ET.Element("AggregationEvent")
        self.create_element(root, "eventTime", eventtime)
        self.create_element(root, "recordTime", recordtime)
        self.create_element(root, "eventTimeZoneOffset", self.offset())

        self.create_element(root, "parentID", f"{parentid}")

        child_epcs = self.create_element(root, "childEPCs")
        for serial_number in serial_numbers:
            self.create_element(child_epcs, "epc", serial_number)

        self.create_element(root, "action", "ADD")
        self.create_element(root, "bizStep", "urn:epcglobal:cbv:bizstep:packing")
        self.create_element(root, "disposition", "urn:epcglobal:cbv:disp:in_progress")

        read_point = self.create_element(root, "readPoint")
        self.create_element(
            read_point,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}",
        )

        biz_location = self.create_element(root, "bizLocation")
        self.create_element(
            biz_location,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}",
        )

        return root  # Return the created event

    def generate_disaggregation_event(
        self, uom_data, eventtime, recordtime, main_root, serial_number = None
    ):
        """
        Generate a disaggregation event.

        This function generates an EPCIS disaggregation event according to the provided data.
        It sets the action to "DELETE", sets the bizstep and disposition based on the
        operation type, and sets the ReadPoint and BizLocation to the sender SGLN.
        It also generates the required ilmd tags and order item details.

        Args:
            uom_data (dict): The UOM data to be used for the disaggregation event.
            eventtime (str): The event time in the format "YYYY-MM-DDTHH:MM:SSZ".
            recordtime (str): The record time in the format "YYYY-MM-DDTHH:MM:SSZ".
            main_root (Element): The main root of the XML tree.
            serial_number (str): The serial number of the object to be disassembled. If None, all serial numbers in uom_data will be used.

        Returns:
            Element: The generated disaggregation event.
        """
        root = ET.Element("AggregationEvent")
        self.create_element(root, "eventTime", eventtime)
        self.create_element(root, "recordTime", recordtime)
        self.create_element(root, "eventTimeZoneOffset", self.offset())
        
        # Fetching Parent URN and Serial Numbers
        parentid = uom_data["parent_urn"]
        serial_numbers = uom_data["urns_format"]

        self.create_element(root, "parentID", f"{parentid}")

        child_epcs = self.create_element(root, "childEPCs")
        if serial_number:
            self.create_element(child_epcs, "epc", serial_number)
        else:
            for serial_number in serial_numbers:
                self.create_element(child_epcs, "epc", serial_number)

        self.create_element(root, "action", "DELETE")
        self.create_element(root, "bizStep", "urn:epcglobal:cbv:bizstep:unpacking")
        self.create_element(root, "disposition", "urn:epcglobal:cbv:disp:in_progress")

        read_point = self.create_element(root, "readPoint")
        self.create_element(
            read_point,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}",
        )

        biz_location = self.create_element(root, "bizLocation")
        self.create_element(
            biz_location,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}",
        )
        return root
    
    def generate_update_event(
        self, uom_data, eventtime, recordtime, main_root, serial_number=None
    ):
        """
        Generate an EPCIS update event according to the provided data.
        This function generates an EPCIS update event according to the provided data.
        It sets the action to "DELETE", sets the bizstep and disposition based on the
        update type and action, and sets the ReadPoint and BizLocation to the sender SGLN.
        It also generates the required ilmd tags and order item details.

        Args:
            uom_data (dict): The UOM data to be used for the update event.
            eventtime (str): The event time in the format "YYYY-MM-DDTHH:MM:SSZ".
            recordtime (str): The record time in the format "YYYY-MM-DDTHH:MM:SSZ".
            main_root (Element): The main root of the XML tree.
            serial_number (str): The serial number of the object to be disassembled. If None, all serial numbers in uom_data will be used.

        Returns:
            Element: The generated update event.
        """
        root = ET.Element("ObjectEvent")
        print("Generating Update Event")
        self.create_element(root, "eventTime", eventtime)
        self.create_element(root, "recordTime", recordtime)
        self.create_element(root, "eventTimeZoneOffset", self.offset())

        # EPC list (serial numbers)
        serial_numbers = uom_data["urns_format"]

        epc_list = self.create_element(root, "epcList")
        if serial_number:
            self.create_element(epc_list, "epc", serial_number)
        else:
            for serial_number in serial_numbers:
                self.create_element(epc_list, "epc", serial_number)

        self.create_element(root, "action", "DELETE")

        print(uom_data)
        update_type = uom_data.get("update_type")
        action = uom_data.get("action", "deactive")
        print(update_type, action)
        if update_type == "DEACTIVATED":
            bizstep, disposition = "destroying", "deactivate"
        else:
            bizstep, disposition = get_update_tags.get((update_type, action), ("decommissioning", "inactive"))

        self.create_element(root, "bizStep", f"urn:epcglobal:cbv:bizstep:{bizstep}")
        self.create_element(root, "disposition", f"urn:epcglobal:cbv:disp:{disposition}")

        read_point = self.create_element(root, "readPoint")
        self.create_element(
            read_point,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}",
        )

        biz_location = self.create_element(root, "bizLocation")
        self.create_element(
            biz_location,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}",
        )

        extension = self.create_element(root, "extension")

        # ilmd tags
        ilmd_list = self.create_element(extension, "ilmd")
        self.create_element(ilmd_list, "cbvmd:lotNumber", self.data.get("lot_number", "default_lot_number"))
        self.create_element(ilmd_list, "cbvmd:manufacturingDate", self.data.get("manufacturing_date", "default_manufacturing_date"))
        self.create_element(ilmd_list, "cbvmd:itemExpirationDate", self.data.get("expiration_date", "default_item_expiration_date"))
        # Add extensionDigit for Bundle, Case, or Pallet
        uom_type = uom_data.get("uom_type", "")
        if uom_type in ["bundle", "case", "pallet"] or uom_type in ["BU", "CA", "PA"]:
            # Extract extension digit from the first serial number (for SSCC URNs)
            extension_digit = None
            if serial_numbers and len(serial_numbers) > 0:
                first_serial = serial_numbers[0]
                # Check if it's an SSCC URN format (starts with 00)
                if first_serial.startswith("urn:epc:id:sscc:"):
                    # Extract from URN: urn:epc:id:sscc:gcp.extensionDigit...
                    urn_parts = first_serial.split(":")
                    if len(urn_parts) >= 5:
                        gcp_extension = urn_parts[4].split(".")
                        if len(gcp_extension) >= 2:
                            extension_digit = gcp_extension[1][0]  # First character after GCP
                else:
                    # Extract from raw serial number (position 2 for SSCC format)
                    # This handles cases where serial_numbers contains raw numbers
                    for number in serial_numbers:
                        if isinstance(number, str) and len(number) > 2 and not number.startswith("urn:"):
                            if number[:2] == "00":  # SSCC format
                                extension_digit = number[2]
                                break
            
            # Use extracted extension digit or fallback to input data
            final_extension_digit = extension_digit or self.data.get("extension_digit", "default_extension_digit")
            self.create_element(ilmd_list, "ah:extensionDigit", final_extension_digit)
        if action != "deactive":
            self.create_element(ilmd_list, "ah:snStatusUpdateReason", action.upper())
        return root


    def initialize_event_timing(self):
        """Initialize event timing with appropriate spread based on total events"""
        # total_events = self.calculate_total_events()
        # Calculate time delta between events (2 seconds)
        # total_seconds_needed = (total_events * 2) + 86400  # 86404 seconds
        # start_time = datetime.utcnow() - timedelta(seconds=total_seconds_needed)
        
        # Set start time to now minus the total time needed
        self.event_timing = {
            'start_time': datetime.utcnow(),
            'current_time': None
        }
        self.event_timing['current_time'] = self.event_timing['start_time']

    def get_next_event_time(self):
        """Get next event time and record time pair"""
        if not self.event_timing:
            self.initialize_event_timing()
            
        self.event_timing['current_time'] += timedelta(milliseconds=2)
        record_time = self.event_timing['current_time'] + timedelta(milliseconds=1)
        
        return (
            self.event_timing['current_time'].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            record_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )

    def generate_delivery_event(
        self, uom_data, eventtime, recordtime, main_root
    ):
        """
        Generate an EPCIS delivery event according to the provided data.
        This function generates an EPCIS delivery event according to the provided data.
        It sets the action to "OBSERVE", sets the bizstep and disposition based on the
        delivery type and delivery status, and sets the ReadPoint and BizLocation to the
        shipping from location. It also generates the required ilmd tags and order item details.

        Args:
            uom_data (dict): The UOM data to be used for the delivery event.
            eventtime (str): The event time in the format "YYYY-MM-DDTHH:MM:SSZ".
            recordtime (str): The record time in the format "YYYY-MM-DDTHH:MM:SSZ".
            main_root (Element): The main root of the XML tree.

        Returns:
            Element: The generated delivery event.
        """
        root = ET.Element("ObjectEvent")
        self.create_element(root, "eventTime", eventtime)
        self.create_element(root, "recordTime", recordtime)
        self.create_element(root, "eventTimeZoneOffset", self.offset())

        # EPC list (serial numbers)
        serial_numbers = uom_data["urns_format"]

        epc_list = self.create_element(root, "epcList")
        for serial_number in serial_numbers:
            self.create_element(epc_list, "epc", serial_number)

        self.create_element(root, "action", "OBSERVE")
        delivery_type = self.data.get("delivery_type")
        delivery_status = self.data.get("delivery_status")
        sale_type = self.data.get('sale_type')
        purchase_type = self.data.get('purchase_type')
        if delivery_type == "OUTBOUND":
            bizstep, disposition = get_delivery_tags.get((delivery_type, delivery_status, sale_type), ("shipping", "in_transit"))
        else:
            bizstep, disposition = get_delivery_tags.get((delivery_type, delivery_status, purchase_type), ("receiving", "active"))
        self.create_element(root, "bizStep", f"urn:epcglobal:cbv:bizstep:{bizstep}")
        self.create_element(root, "disposition", f"urn:epcglobal:cbv:disp:{disposition}")

        read_point = self.create_element(root, "readPoint")
        self.create_element(
            read_point,
            "id",
            f"urn:epc:id:sgln:{self.data.get('shipping_from_location', 'default_sgln')}",
        )

        biz_location = self.create_element(root, "bizLocation")
        self.create_element(
            biz_location,
            "id",
            f"urn:epc:id:sgln:{self.data.get('shipping_from_business', 'default_sgln')}",
        )


        biz_transaction_list = self.create_element(root, 'bizTransactionList')
        delivery_tag = "desadv" if delivery_type == "OUTBOUND" else "recadv"
        transaction_type = ET.SubElement(
            biz_transaction_list,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}bizTransaction",
            {"type": f"urn:epcglobal:cbv:btt:{delivery_tag}"},
        )
        transaction_type.text = (
            f"urn:epcglobal:cbv:bt:{self.data.get('shipping_from_location', 'default_sgln')}:{self.data.get('delivery_number', 'default_delivery_number')}"
        )

        for identifier in self.data.get("transaction_identifiers", []):
            identifier_type = identifier.get("type")
            identifier_value = identifier.get("value")
            identifier_tag = get_identifier_tag.get(identifier_type, "shipment")
            transaction_value = ET.SubElement(
                biz_transaction_list,
                "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}bizTransaction",
                {"type": f"urn:epcglobal:cbv:btt:{identifier_tag}"},
            )
            transaction_value.text = (
                f"urn:epcglobal:cbv:bt:{self.data.get('shipping_from_location', 'default_sgln')}:{identifier_value}"
            )

        extension = self.create_element(root, "extension")

        # sourceList Tag
        source_list = self.create_element(extension, "sourceList")
        from_location = ET.SubElement(
            source_list,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}source",
            {"type": "urn:epcglobal:cbv:sdt:location"},
        )
        from_location.text = (
            f"urn:epc:id:sgln:{self.data.get('shipping_from_location', 'default_sgln')}"
        )
        from_business = ET.SubElement(
            source_list,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}source",
            {"type": "urn:epcglobal:cbv:sdt:owning_party"},
        )
        from_business.text = (
            f"urn:epc:id:sgln:{self.data.get('shipping_from_business', 'default_sgln')}"
        )

        # destinationList Tag
        destination_list = self.create_element(extension, "destinationList")
        to_location = ET.SubElement(
            destination_list,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}destination",
            {"type": "urn:epcglobal:cbv:sdt:location"},
        )
        to_location.text = (
            f"urn:epc:id:sgln:{self.data.get('shipping_to_location', 'default_sgln')}"
        )
        to_business = ET.SubElement(
            destination_list,
            "{http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader}destination",
            {"type": "urn:epcglobal:cbv:sdt:owning_party"},
        )
        to_business.text = (
            f"urn:epc:id:sgln:{self.data.get('shipping_to_business', 'default_sgln')}"
        )

        # ilmd tags
        ilmd_list = self.create_element(extension, "ilmd")
        self.create_element(ilmd_list, "ah:shipmentDate", self.data.get('shipment_date', 'default_shipment_date'))
        if self.data.get('delivery_type') == "OUTBOUND":
            self.create_element(ilmd_list, "ah:saleType", self.data.get('sale_type', 'default_sale_type'))
        elif self.data.get('delivery_type') == "INBOUND":
            self.create_element(ilmd_list, "ah:purchaseType", self.data.get('purchase_type', 'default_purchase_type'))
        self.create_element(ilmd_list, "ah:deliveryStatus", self.data.get('delivery_status', 'default_delivery_status'))
        self.create_element(ilmd_list, "ah:fromCountry", self.data.get('shipping_from_country', 'default_from_country'))
        self.create_element(ilmd_list, "ah:toCountry", self.data.get('shipping_to_country', 'default_to_country'))
        # self.create_element(ilmd_list, "ah:fromPort", self.data.get('from_port', 'default_from_port'))
        # self.create_element(ilmd_list, "ah:toPort", self.data.get('to_port', 'default_to_port'))
        # self.create_element(ilmd_list, "ah:portalAccessCode", self.data.get('portal_access_code', 'default_portal_access_code'))
        self.create_element(ilmd_list, "cbvmd:lotNumber", self.data.get('lot_number', 'default_lot_number'))

        # TODO: Not Required as of now
        # contract_details = self.create_element(ilmd_list, "ah:contractDetails")
        # self.create_element(contract_details, "ah:typeOfContract", self.data.get('type_of_contract', 'default_type_of_contract'))
        # self.create_element(contract_details, "ah:contractNumber", self.data.get('contract_number', 'default_contract_number'))
        # self.create_element(contract_details, "ah:typeofSupply", self.data.get('type_of_supply', 'default_type_of_supply'))
        # self.create_element(contract_details, "ah:sourceOfFunding", self.data.get('source_of_funding', 'default_source_of_funding'))
        # self.create_element(contract_details, "ah:removalfromCirculation", self.data.get('removal_from_circulation', 'default_removal_from_circulation'))
        # self.create_element(contract_details, "ah:remarks", self.data.get('remarks', 'default_remarks'))

        serial_number_details = self.create_element(ilmd_list, "ah:serialNumberDetails")
        # self.create_element(serial_number_details, "ah:warehouseOperator", self.data.get('warehouse_operator', 'New operator'))
        # self.create_element(serial_number_details, "ah:inspectionofAggregation", self.data.get('inspection_of_aggregation', 'Verified'))
        # self.create_element(serial_number_details, "ah:inspectionDelivery", self.data.get('inspection_delivery', 'Inspection Failed'))
        # self.create_element(serial_number_details, "ah:deliveryInspectionDate", self.data.get('delivery_inspection_date', self.data.get('shipment_date')))
        # self.create_element(serial_number_details, "ah:remarks", self.data.get('remarks', 'New operator'))
        self.create_element(serial_number_details, "ah:serialNumberScanning", self.data.get('serial_number_scanning', 'true'))
        self.create_element(serial_number_details, "ah:lotNumberWise", self.data.get('lot_number_wise', 'false'))

        # TODO: Not Required as of now
        # transportation_carriers_list = self.create_element(ilmd_list, "ah:transportationCarriersList")
        # self.create_element(transportation_carriers_list, "ah:nameOfCarrier", self.data.get('name_of_carrier', 'default_name_of_carrier'))

        order_item_details_list = self.create_element(ilmd_list, "ah:orderItemDetailsList")
        order_details = self.create_element(order_item_details_list, "ah:orderDetails")
        self.create_element(order_details, "ah:itemCode", self.data.get('item_code', 'default_item_code'))
        self.create_element(order_details, "ah:isItemSerialized", self.data.get('true', 'true'))
        # quantity = len(self.data.get("modules", {}).get("WHD", {}).get("inbound", {}).get("file", {}).get("urns", [])) or len(self.data.get("modules", {}).get("WHD", {}).get("inbound", {}).get("file", {}).get("urns", []))
        # self.create_element(order_details, "ah:quantity", str(quantity))
        # self.create_element(order_details, "ah:orderItemNumber", self.data.get('order_item_number', 'default_order_item_number'))
        self.create_element(order_details, "cbvmd:lotNumber", self.data.get('lot_number', 'default_lot_number'))
        self.create_element(order_details, "cbvmd:itemExpirationDate", self.data.get('expiration_date', 'default_item_expiration_date'))
        # self.create_element(order_details, "ah:currencyPrice", self.data.get('currency_price', "ALL"))
        # self.create_element(order_details, "ah:isItemSerialized", self.data.get('is_item_serialized', 'true'))

        transaction_identifier_list = self.create_element(order_details, "ah:transactionIdentifiersList")
        for identifier in self.data.get("transaction_identifiers", []):
            identifier_type = identifier.get("type")
            identifier_value = identifier.get("value")
            identifier_tag = get_identifier_tag.get(identifier_type, "shipment")
            self.create_element(transaction_identifier_list, "ah:transactionIdentifierType", identifier_type)
            self.create_element(transaction_identifier_list, "ah:transactionIdentifierValue", identifier_value)

        return root

    def generate_sampling_event(self, urns, eventtime, recordtime, sn_status_update_reason=None, inspection_country=None, sampling_entity=None, sampling_reason=None):
        """
        Generate a product sampling ObjectEvent for SPO.
        Args:
            urns (list): List of EPC URNs to be observed (sampled).
            eventtime (str): The event time in ISO format.
            recordtime (str): The record time in ISO format.
            sn_status_update_reason (str): Reason for status update (optional, for ilmd).
            inspection_country (str): Country of inspection (optional, for ilmd).
            sampling_entity (str): Entity performing sampling (optional, for ilmd).
            sampling_reason (str): Reason for sampling (optional, for ilmd).
        Returns:
            Element: The generated ObjectEvent for product sampling.
        """
        root = ET.Element("ObjectEvent")
        self.create_element(root, "eventTime", eventtime)
        self.create_element(root, "recordTime", recordtime)
        self.create_element(root, "eventTimeZoneOffset", self.offset())

        # EPC list (multiple URNs)
        epc_list = self.create_element(root, "epcList")
        for urn in urns:
            self.create_element(epc_list, "epc", urn)

        # Action, bizStep, disposition for sampling
        self.create_element(root, "action", "OBSERVE")
        self.create_element(root, "bizStep", "urn:epcglobal:cbv:bizstep:sampling")
        self.create_element(root, "disposition", "urn:epcglobal:cbv:disp:in_progress")

        # ReadPoint and BizLocation (use sender_sgln)
        read_point = self.create_element(root, "readPoint")
        self.create_element(
            read_point,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}"
        )
        biz_location = self.create_element(root, "bizLocation")
        self.create_element(
            biz_location,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}"
        )

        # Extension with ilmd tags for sampling
        extension = self.create_element(root, "extension")
        ilmd = self.create_element(extension, "ilmd")
        if sn_status_update_reason:
            self.create_element(ilmd, "ah:snStatusUpdateReason", sn_status_update_reason)
        if inspection_country:
            self.create_element(ilmd, "ah:inspectionCountry", inspection_country)
        if sampling_entity:
            self.create_element(ilmd, "ah:samplingEntity", sampling_entity)
        if sampling_reason:
            self.create_element(ilmd, "ah:samplingReason", sampling_reason)

        return root
    
    def generate_destruction_event(self, urns, eventtime, recordtime, sn_status_update_reason=None, description=None, destruction_reason=None, destruction_method=None):
        """
        Generate a product destruction ObjectEvent for SPO.
        Args:
            urns (list): List of EPC URNs to be destroyed.
            eventtime (str): The event time in ISO format.
            recordtime (str): The record time in ISO format.
            sn_status_update_reason (str): Reason for status update (optional, for ilmd).
            description (str): Description of the destruction (optional, for ilmd).
            destruction_reason (str): Reason for destruction (optional, for ilmd).
            destruction_method (str): Method of destruction (optional, for ilmd).
        Returns:
            Element: The generated ObjectEvent for product destruction.
        """
        root = ET.Element("ObjectEvent")
        self.create_element(root, "eventTime", eventtime)
        self.create_element(root, "recordTime", recordtime)
        self.create_element(root, "eventTimeZoneOffset", self.offset())

        # EPC list (multiple URNs)
        epc_list = self.create_element(root, "epcList")
        for urn in urns:
            self.create_element(epc_list, "epc", urn)

        # Action, bizStep, disposition for destruction
        self.create_element(root, "action", "DELETE")
        self.create_element(root, "bizStep", "urn:epcglobal:cbv:bizstep:destroying")
        self.create_element(root, "disposition", "urn:epcglobal:cbv:disp:destroyed")

        # ReadPoint and BizLocation (use sender_sgln)
        read_point = self.create_element(root, "readPoint")
        self.create_element(
            read_point,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}"
        )
        biz_location = self.create_element(root, "bizLocation")
        self.create_element(
            biz_location,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}"
        )

        # Extension with ilmd tags for destruction
        extension = self.create_element(root, "extension")
        ilmd = self.create_element(extension, "ilmd")
        # if sn_status_update_reason:
        #     self.create_element(ilmd, "ah:snStatusUpdateReason", sn_status_update_reason)
        if description:
            self.create_element(ilmd, "ah:description", description)
        if destruction_reason:
            self.create_element(ilmd, "ah:snStatusUpdateReason", destruction_reason)
            self.create_element(ilmd, "ah:destructionReason", destruction_reason)
        if destruction_method:
            self.create_element(ilmd, "ah:destructionMethod", destruction_method)

        return root
    
    def generate_decommissioning_event(self, urns, eventtime, recordtime, decommissioning_reason=None, decommissioning_description=None):
        """
        Generate a product decommissioning ObjectEvent for SPO.
        Args:
            urns (list): List of EPC URNs to be decommissioned.
            eventtime (str): The event time in ISO format.
            recordtime (str): The record time in ISO format.
            decommissioning_reason (str): Reason for decommissioning (for ilmd).
            decommissioning_description (str): Description for decommissioning (for ilmd).
        Returns:
            Element: The generated ObjectEvent for product decommissioning.
        """
        root = ET.Element("ObjectEvent")
        self.create_element(root, "eventTime", eventtime)
        self.create_element(root, "recordTime", recordtime)
        self.create_element(root, "eventTimeZoneOffset", self.offset())

        # EPC list (multiple URNs)
        epc_list = self.create_element(root, "epcList")
        for urn in urns:
            self.create_element(epc_list, "epc", urn)

        # Action, bizStep, disposition for decommissioning
        self.create_element(root, "action", "DELETE")
        self.create_element(root, "bizStep", "urn:epcglobal:cbv:bizstep:decommissioning")
        self.create_element(root, "disposition", "urn:epcglobal:cbv:disp:inactive")

        # ReadPoint and BizLocation (use sender_sgln)
        read_point = self.create_element(root, "readPoint")
        self.create_element(
            read_point,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}"
        )
        biz_location = self.create_element(root, "bizLocation")
        self.create_element(
            biz_location,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}"
        )

        # Extension with ilmd tags for decommissioning
        extension = self.create_element(root, "extension")
        ilmd = self.create_element(extension, "ilmd")
        self.create_element(ilmd, "ah:decommissioningReason", decommissioning_reason or "")
        self.create_element(ilmd, "ah:decommissioningDescription", decommissioning_description or "default_description")

        return root

    def generate_production_event(self, uom_data, eventtime, recordtime, main_root):
        """
        Generate a production event.

        This function generates an EPCIS production event according to the provided data.
        It sets the action to "OBSERVE", sets the bizstep and disposition based on the
        operation type, and sets the ReadPoint and BizLocation to the sender SGLN.
        It also generates the required ilmd tags and order item details.

        Args:
            uom_data (dict): The UOM data to be used for the production event.
            eventtime (str): The event time in the format "YYYY-MM-DDTHH:MM:SSZ".
            recordtime (str): The record time in the format "YYYY-MM-DDTHH:MM:SSZ".
            main_root (Element): The main root of the XML tree.

        Returns:
            Element: The generated production event.
        """
        root = ET.Element("ObjectEvent")
        self.create_element(root, "eventTime", eventtime)
        self.create_element(root, "recordTime", recordtime)
        self.create_element(root, "eventTimeZoneOffset", self.offset())

        self.create_element(root, "action", "OBSERVE")
        operation = self.data.get("operation_type")
        common = "end_of_lot" if operation == "End of Lot" else "reopen_lot"
        self.create_element(root, "bizStep", f"urn:epcglobal:cbv:bizstep:{common}")
        self.create_element(root, "disposition", f"urn:epcglobal:cbv:disp:{common}")

        # ReadPoint and BizLocation
        read_point = self.create_element(root, "readPoint")
        self.create_element(
            read_point,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}",
        )

        biz_location = self.create_element(root, "bizLocation")
        self.create_element(
            biz_location,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}",
        )

        extension = self.create_element(root, "extension")

        # ilmd tags
        ilmd_list = self.create_element(extension, "ilmd")
        self.create_element(
            ilmd_list,
            "cbvmd:lotNumber",
            self.data.get("lot_number", "ABCD"),
        )
        lot_details = self.create_element(ilmd_list, "ah:lotDetails")
        self.create_element(lot_details, "ah:itemCodeType", self.data.get("item_code_type", "Internal Material Code"))
        self.create_element(lot_details, "ah:itemCodeValue", self.data.get("item_code_value", "987654321"))
        self.create_element(lot_details, "ah:countryCode", self.data.get("country_code", "IN"))
        if operation == "End of Lot":    
            # Map level names to UOM codes
            level_to_uom = {
                "each": "EA",
                "inner": "BU",
                "case": "CA",
                "pallet": "PA"
            }
            packaging_code_detail_list = self.create_element(lot_details, "ah:packagingCodeDetailList")
            for p_code in self.data.get("packaging", []):
                packaging_code = p_code.get("packaging_code", "987654321")
                # Try to infer UOM from level if present, else fallback to provided uom_level or 'EA'
                level = p_code.get("level")
                if level and level.lower() in level_to_uom:
                    uom_level = level_to_uom[level.lower()]
                else:
                    uom_level = p_code.get("uom_level", "EA")
                quantity = p_code.get("quantity", "1")
                packaging_code_details = self.create_element(packaging_code_detail_list, "ah:packagingCodeDetails")
                self.create_element(packaging_code_details, "ah:packagingCodeValue", packaging_code)
                self.create_element(packaging_code_details, "ah:packagingUOM", uom_level)
                self.create_element(packaging_code_details, "ah:quantity", quantity)

        return root
    
    def get_spo_update_event_params(self, current_state, target_state, current_logistic, target_logistic, reason):
        # Normalize string "None" to Python None for comparison
        def normalize_none(value):
            return None if value == "None" else value
        
        current_logistic_norm = normalize_none(current_logistic)
        target_logistic_norm = normalize_none(target_logistic)
        
        for rule in SPO_STATUS_UPDATE_SCENARIOS:
            rule_current_logistic = normalize_none(rule["current_logistic"])
            rule_target_logistic = normalize_none(rule["target_logistic"])
            
            if (
                rule["current_state"] == current_state and
                rule["target_state"] == target_state and
                (rule_current_logistic == current_logistic_norm or rule_current_logistic is None) and
                (rule_target_logistic == target_logistic_norm or rule_target_logistic is None) and
                rule["reason"] == reason
            ):
                return rule["actions"], rule["bizsteps"], rule["dispositions"]
        return None, None, None
    
    def generate_status_update_event_scenario(self, urns, eventtime, recordtime, action, bizstep, disposition, reason, update_type=None):
        root = ET.Element("ObjectEvent")
        self.create_element(root, "eventTime", eventtime)
        self.create_element(root, "recordTime", recordtime)
        self.create_element(root, "eventTimeZoneOffset", self.offset())
        epc_list = self.create_element(root, "epcList")
        for urn in urns:
            self.create_element(epc_list, "epc", urn)
        self.create_element(root, "action", action)
        self.create_element(root, "bizStep", f"urn:epcglobal:cbv:bizstep:{bizstep}")
        self.create_element(root, "disposition", f"urn:epcglobal:cbv:disp:{disposition}")
        read_point = self.create_element(root, "readPoint")
        self.create_element(
            read_point,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}"
        )
        biz_location = self.create_element(root, "bizLocation")
        self.create_element(
            biz_location,
            "id",
            f"urn:epc:id:sgln:{self.data.get('sender_sgln', 'default_sgln')}"
        )
        extension = self.create_element(root, "extension")
        ilmd = self.create_element(extension, "ilmd")
        # Convert reason to uppercase for XML
        reason_upper = (reason or "").upper()
        self.create_element(ilmd, "ah:snStatusUpdateReason", reason_upper)
        if update_type:
            # Convert update_type to uppercase format for XML
            if update_type == "Update of Product Status":
                xml_update_type = "UPDATE_PRODUCT_STATUS"
            elif update_type == "Correction of incorrect product status":
                xml_update_type = "CORRECTION_PRODUCT_STATUS"
            else:
                # Fallback: convert any other format to uppercase with underscores
                xml_update_type = update_type.upper().replace(" ", "_")
            self.create_element(ilmd, "ah:updateType", xml_update_type)
        self.create_element(ilmd, "cbvmd:lotNumber", self.data.get("lot_number", "default_lot_number"))
        self.create_element(ilmd, "cbvmd:manufacturingDate", self.data.get("manufacturing_date", "default_manufacturing_date"))
        self.create_element(ilmd, "cbvmd:itemExpirationDate", self.data.get("expiration_date", "default_item_expiration_date"))
        return root


    def generate_scenario_status_update_events(self, scenarios):
        """
        Generate ObjectEvents for SPO status updates based on scenario rules.
        Args:
            scenarios (list): List of dicts, each with keys:
                urns, current_state, target_state, current_logistic, target_logistic, reason, update_type
        Returns:
            list: List of generated ObjectEvent elements.
        """
        events = []
        for scenario in scenarios:
            urns = scenario.get("urns", [])
            cur = scenario.get("current_state")
            tgt = scenario.get("target_state")
            cur_log = scenario.get("current_logistic")
            tgt_log = scenario.get("target_logistic")
            reason = scenario.get("reason")
            update_type = scenario.get("update_type", "Update of Product Status")
            actions, bizsteps, dispositions = self.get_spo_update_event_params(cur, tgt, cur_log, tgt_log, reason)
            if not actions:
                continue  # Or log error/warning
            for action, bizstep, disposition in zip(actions, bizsteps, dispositions):
                event_time, record_time = self.get_next_event_time()
                event = self.generate_status_update_event_scenario(
                    urns, event_time, record_time, action, bizstep, disposition, reason, update_type
                )
                events.append(event)
        return events


    
    def generate_epcis_body(self):
        """
        Generate EPCIS XML body with commissioning and aggregation handled together (parent-child mapping),
        then other event types. This matches the previous logic for parent-child event sequencing.
        Returns:
            ET.Element: Root element containing all EPCIS events
        """
        try:
            root = ET.Element("EPCISBody")
            event_list = ET.SubElement(root, "EventList")

            # --- Commissioning & Aggregation: classic parent-child (e.g., each->inner, inner->case, case->pallet) ---
            commissioning_data = self.data.get("modules", {}).get("SNI", {}).get("commissioning", {})
            # UOM mapping
            UOM_TYPE_DICT = {
                "each": "EA",
                "inner": "BU",
                "case": "CA",
                "pallet": "PA",
            }

            UOM_LIST = ["each", "inner", "case", "pallet"]

            def process_object_events(level_name, level_data):
                """
                Commission object events for a given packaging level.
                Handles both batch and individual commissioning.
                """
                events = []
                urns = level_data.get("urns", [])

                if not urns:
                    return events

                # If consolidated commissioning (all in one event)
                if level_data.get("file_type") == "CONSOLIDATED_TIME":
                    object_type = "01" if urns[0].startswith("urn:epc:id:sgtin:") else "00"
                    event_time, record_time = self.get_next_event_time()
                    obj_event = self.generate_object_event(
                        object_type,
                        event_time,
                        record_time,
                        None,
                        urns,
                        UOM_TYPE_DICT.get(level_name, level_name.upper()),
                    )
                    events.append(obj_event)
                    self.processed_data.extend(urns)
                else:
                    # Commission one by one
                    for urn in urns:
                        object_type = "01" if urn.startswith("urn:epc:id:sgtin:") else "00"
                        event_time, record_time = self.get_next_event_time()
                        obj_event = self.generate_object_event(
                            object_type,
                            event_time,
                            record_time,
                            None,
                            [urn],
                            UOM_TYPE_DICT.get(level_name, level_name.upper()),
                        )
                        events.append(obj_event)
                        self.processed_data.append(urn)

                return events

            # Step 1: Commission object events for all available levels
            for level_name in UOM_LIST:
                if level_name not in commissioning_data:
                    continue
                level_events = process_object_events(level_name, commissioning_data[level_name])
                event_list.extend(level_events)

            # Step 2: Aggregation events (child → parent)
            available_levels = [lvl for lvl in UOM_LIST if lvl in commissioning_data]

            for i in range(1, len(available_levels)):  # skip first (each)
                parent_level = available_levels[i]
                child_level = available_levels[i - 1]

                parent_data = commissioning_data[parent_level]
                child_data = commissioning_data[child_level]

                parent_urns = parent_data.get("urns", [])
                child_urns = child_data.get("urns", [])

                pack_size = int(parent_data.get("pack_size", 1))

                for j, parent_urn in enumerate(parent_urns):
                    start = j * pack_size
                    end = min(start + pack_size, len(child_urns))
                    child_group = child_urns[start:end]

                    if child_group:
                        event_time, record_time = self.get_next_event_time()
                        agg_event = self.generate_aggregation_event(
                            parent_urn,
                            event_time,
                            record_time,
                            event_list,
                            child_group,
                        )
                        event_list.append(agg_event)

            # --- Disaggregation Events ---
            disaggregation_data = self.data.get("modules", {}).get("SNI", {}).get("disaggregation", [])
            for disagg in disaggregation_data:
                parent_file = disagg.get("parent_file", {})
                child_file = disagg.get("child_file", {})
                parent_urns = parent_file.get("urns", [])
                child_urns = child_file.get("urns", [])
                for parent_urn in parent_urns:
                    event_time, record_time = self.get_next_event_time()
                    disagg_event = self.generate_disaggregation_event(
                        {"parent_urn": parent_urn, "urns_format": child_urns},
                        event_time,
                        record_time,
                        None
                    )
                    event_list.append(disagg_event)

            # --- Update Events ---
            update_data = self.data.get("modules", {}).get("SNI", {}).get("update", {})
            if update_data and update_data.get("urns"):
                urns = update_data.get("urns", [])
                update_type = update_data.get("update_type", "")
                action = update_data.get("action", "")
                uom_type = update_data.get("uom_type", "")
                
                # Commissioning object event before status update (only if not DEACTIVATED)
                if update_type != "DEACTIVATED":
                    event_time, record_time = self.get_next_event_time()
                    object_type = "01" if urns[0].startswith("urn:epc:id:sgtin:") else "00"
                    commissioning_event = self.generate_object_event(
                        object_type,
                        event_time,
                        record_time,
                        None,
                        urns,
                        UOM_TYPE_DICT.get(uom_type.lower(), uom_type.upper())
                    )
                    event_list.append(commissioning_event)
                
                # Now do the update event
                event_time, record_time = self.get_next_event_time()
                update_event = self.generate_update_event(
                    {"urns_format": urns, "update_type": update_type, "action": action},
                    event_time,
                    record_time,
                    None
                )
                event_list.append(update_event)

            # --- Serial Product Operations (SPO) Events ---
            spo_data = self.data.get("modules", {}).get("SPO", {})
            # Decommissioning Events
            decommissioning_data = spo_data.get("decommissioning", {})
            if decommissioning_data and decommissioning_data.get("urns"):
                urns = decommissioning_data.get("urns", [])
                reason = decommissioning_data.get("reason", "")
                # Always pass a list to generate_decommissioning_event
                if isinstance(urns, str):
                    urns = [urns]
                event_time, record_time = self.get_next_event_time()
                decom_event = self.generate_decommissioning_event(
                    urns,
                    event_time,
                    record_time,
                    reason
                )
                event_list.append(decom_event)
            # Destruction Events
            destruction_data = spo_data.get("destruction", {})
            if destruction_data and destruction_data.get("urns"):
                urns = destruction_data.get("urns", [])
                reason = destruction_data.get("reason", "")
                method = destruction_data.get("method", "")
                description = destruction_data.get("description", "default description")
                event_time, record_time = self.get_next_event_time()
                destruction_event = self.generate_destruction_event(
                    urns,
                    event_time,
                    record_time,
                    None,
                    description,
                    reason,
                    method
                )
                event_list.append(destruction_event)

            # Sampling Events
            sampling_data = spo_data.get("sampling", {})
            if sampling_data and sampling_data.get("urns"):
                urns = sampling_data.get("urns", [])
                # Optionally, add more ilmd fields if present in sampling_data
                sn_status_update_reason = sampling_data.get("sn_status_update_reason")
                inspection_country = sampling_data.get("inspection_country")
                sampling_entity = sampling_data.get("sampling_entity")
                sampling_reason = sampling_data.get("sampling_reason")
                if urns:
                    event_time, record_time = self.get_next_event_time()
                    sampling_event = self.generate_sampling_event(
                        urns,
                        event_time,
                        record_time,
                        sn_status_update_reason,
                        inspection_country,
                        sampling_entity,
                        sampling_reason
                    )
                    event_list.append(sampling_event)

            # Status Update Events (old logic)
            status_update_data = spo_data.get("status_update", {})
            if status_update_data and status_update_data.get("urns"):
                urns = status_update_data.get("urns", [])
                serial_status = status_update_data.get("serial_status", "")
                logistic_status = status_update_data.get("logistic_status", "")
                update_reason = status_update_data.get("reason", "")
                update_type = status_update_data.get("update_type", "")
                for urn in urns:
                    event_time, record_time = self.get_next_event_time()
                    status_event = self.generate_status_update_event(
                        urn,
                        event_time,
                        record_time,
                        serial_status,
                        logistic_status,
                        update_reason,
                        update_type
                    )
                    event_list.append(status_event)

            # Scenario-based SPO Status Update Events (new logic)
            # Support both 'spo_update' and 'status_update["scenarios"]' for backward compatibility
            spo_update_scenarios = []
            if "spo_update" in spo_data:
                spo_update_scenarios = spo_data.get("spo_update", [])
            elif "status_update" in spo_data and "scenarios" in spo_data["status_update"]:
                spo_update_scenarios = spo_data["status_update"]["scenarios"]
            if spo_update_scenarios:
                scenario_events = self.generate_scenario_status_update_events(spo_update_scenarios)
                event_list.extend(scenario_events)


            # --- Warehouse Delivery (WHD) Events ---
            whd_data = self.data.get("modules", {}).get("WHD", {})
            for direction in ["inbound", "outbound"]:
                direction_data = whd_data.get(direction, {})
                if not direction_data:
                    continue
                urns = direction_data.get("urns", [])
                if not urns:
                    continue
                transaction_identifiers = direction_data.get("transaction_identifiers", [])
                event_time, record_time = self.get_next_event_time()
                import copy
                original_data = copy.deepcopy(self.data)
                try:
                    self.data = {
                        **direction_data,
                        "transaction_identifiers": transaction_identifiers,
                        "UOM_delivery": {
                            "urns_format": urns,
                            "delivery_type": direction.upper()
                        },
                        # Preserve essential fields from original data
                        "expiration_date": original_data.get("expiration_date"),
                        "manufacturing_date": original_data.get("manufacturing_date"),
                        "lot_number": original_data.get("lot_number"),
                        "sender_sgln": original_data.get("sender_sgln"),
                        "receiver_sgln": original_data.get("receiver_sgln"),
                        "extension_digit": original_data.get("extension_digit"),
                        "gcp": original_data.get("gcp")
                    }
                    delivery_event = self.generate_delivery_event(
                        {"urns_format": urns, "delivery_type": direction.upper()},
                        event_time,
                        record_time,
                        None
                    )
                    event_list.append(delivery_event)
                finally:
                    self.data = original_data


            # --- Batch Production Management (BPM) Events ---
            bpm_data = self.data.get("modules", {}).get("BPM", {})
            # Detect the operation from what's present in the BPM data
            if bpm_data:
                if "reopen_lot" in bpm_data:
                    op_key = "reopen_lot"
                    selected_op = "Re-open Lot"
                    op_data = bpm_data[op_key]
                elif "end_of_lot" in bpm_data:
                    op_key = "end_of_lot"
                    selected_op = "End of Lot"
                    op_data = bpm_data[op_key]
                else:
                    op_key = None
                    selected_op = None
                    op_data = None

                if op_data:
                    import copy
                    original_data = copy.deepcopy(self.data)
                    try:
                        self.data = {**self.data, **op_data, "operation_type": selected_op}
                        event_time, record_time = self.get_next_event_time()
                        prod_event = self.generate_production_event({}, event_time, record_time, None)
                        event_list.append(prod_event)
                    finally:
                        self.data = original_data

            return root

        except Exception as e:
            print(f"[ERROR] Failed to generate EPCIS body: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Error generating EPCIS body: {str(e)}")

    def save_epcis_document(self, output_file_path):
        """
        Generates the EPCIS document and saves it to the specified file path.
        This method is called directly by the external Bash script.

        Args:
            output_file_path (str): The path where the XML file should be saved.
        """
        try:
            # Generate the XML tree from your existing method
            epcis_doc = self.generate_epcis_document()
            
            # Create an ElementTree object and write to file with proper declaration
            tree = ET.ElementTree(epcis_doc)
            
            # If no output path provided, create a default timestamped file in EPCISfiles/
            if not output_file_path or not isinstance(output_file_path, str):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                default_dir = os.path.join(os.getcwd(), "EPCISfiles")
                os.makedirs(default_dir, exist_ok=True)
                output_file_path = os.path.join(default_dir, f"epcis_{timestamp}.xml")

            # Create the directory if it doesn't exist
            dir_name = os.path.dirname(output_file_path)
            if not dir_name:
                dir_name = os.getcwd()
            os.makedirs(dir_name, exist_ok=True)
            
            # Write to file with XML declaration and proper encoding
            tree.write(output_file_path, 
                    encoding='utf-8', 
                    xml_declaration=True, 
                    method='xml')
            
            print(f"EPCIS document successfully saved to: {output_file_path}")
            return {"status": "success", "output_file": output_file_path}
            
        except Exception as e:
            error_msg = f"Failed to save EPCIS document: {str(e)}"
            print(error_msg)
            return {"status": "error", "message": error_msg}

    def _infer_uom_from_urn(self, urn, level_to_uom):
        # Helper to infer UOM from URN pattern or fallback to EA
        # You can expand this logic as needed
        if ":sgtin:" in urn:
            return "EA"
        elif ":sscc:" in urn:
            return "PA"
        return "EA"

