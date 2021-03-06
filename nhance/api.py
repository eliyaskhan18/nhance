from __future__ import unicode_literals
import frappe
from frappe import _, throw, msgprint, utils
from frappe.utils import cint, flt, cstr, comma_or, getdate, add_days, getdate, rounded, date_diff, money_in_words
from frappe.model.mapper import get_mapped_doc
from frappe.model.naming import make_autoname
from erpnext.utilities.transaction_base import TransactionBase
from erpnext.accounts.party import get_party_account_currency
from frappe.desk.notifications import clear_doctype_notifications
from datetime import datetime
import sys
import os
import operator
import frappe
import json
import time
import math
import base64
import ast

@frappe.whitelist()
def make_proposal_stage(source_name, target_doc=None):


	target_doc = get_mapped_doc("Opportunity", source_name, {
		"Opportunity": {
			"doctype": "Proposal Stage",
			"field_map": {
				"doctype": "stage_doctype",
				"name": "document_number"
			 }
		}
	
	}, target_doc, set_missing_values)


	return target_doc

@frappe.whitelist()
def make_proposal_stage_q(source_name, target_doc=None):


	target_doc = get_mapped_doc("Quotation", source_name, {
		"Quotation": {
			"doctype": "Proposal Stage",
			"field_map": {
				"name": "document_number",
				"doctype": "stage_doctype"
			 }
		}
	
	}, target_doc, set_missing_values)


	return target_doc

@frappe.whitelist()
def make_interactions(source_name, target_doc=None):

	target_doc = get_mapped_doc("Opportunity", source_name, {
		"Opportunity": {
			"doctype": "Interactions",
			"field_map": {
				"name": "opportunity"

				}
		}
		
	}, target_doc, set_missing_values)

	return target_doc

@frappe.whitelist()
def make_interactions_quot(source_name, target_doc=None):
	src_name = "Quotation"
	target_doc = get_mapped_doc("Quotation", source_name, {
		"Quotation": {
			"doctype": "Interactions",
			"field_map": {
				"name": "quotation"
				}
		}
		
	}, target_doc, set_missing_values)

	return target_doc

@frappe.whitelist()
def make_interactions_so(source_name, target_doc=None):
	src_name = "Sales Order"
	target_doc = get_mapped_doc("Sales Order", source_name, {
		"Sales Order": {
			"doctype": "Interactions",
			"field_map": {
				"name": "sales_order"

				}
		}
		
	}, target_doc, set_missing_values)

	return target_doc

@frappe.whitelist()
def make_interactions_si(source_name, target_doc=None):
	src_name = "Sales Invoice"
	target_doc = get_mapped_doc("Sales Invoice", source_name, {
		"Sales Invoice": {
			"doctype": "Interactions",
			"field_map": {
				"name": "sales_invoice",
				}
		}
		
	}, target_doc, set_missing_values)

	return target_doc

@frappe.whitelist()
def make_interactions_cust(source_name, target_doc=None):
	src_name = "Customer"
	target_doc = get_mapped_doc("Customer", source_name, {
		"Customer": {
			"doctype": "Interactions",
			"field_map": {
				"name": "customer"

				}
		}
		
	}, target_doc, set_missing_values)

	return target_doc



@frappe.whitelist()
def set_proposal_stage_values(opportunity):

        
	max_closing_date = frappe.db.sql("""select max(closing_date) from `tabProposal Stage` where reference_name=%s""",
				(opportunity))
				
        sc_rec = frappe.db.sql("""select value, closing_date, stage, opportunity_purpose, buying_status, support_needed, competition_status
		from `tabProposal Stage`
		where reference_name=%s and closing_date = %s""",
		(opportunity, max_closing_date))
        return sc_rec

#@frappe.whitelist()
#def set_opp_stages(opportunity):

#	opp_record = frappe.get_doc("Opportunity", opportunity)
#	frappe.msgprint(_(opp_record.name))
#	check_field = 0
        
#	stage_records = frappe.db.sql("""select name as stage_name, opportunity_purpose, buying_status, closing_date, stage, value, competition_status, support_needed from `tabProposal Stage` where document_number=%s""", (opportunity), as_dict = 1)
#	frappe.msgprint(_(stage_records))
#	for row in stage_records:
#		check_field = 0
#		frappe.msgprint(_(row.stage_name))
#		for record in opp_record.opp_stage:
#			frappe.msgprint(_(record))
#			if row.stage_name == record.stage_name:
#				check_field = 1
#		frappe.msgprint(_(row.name))
#		if chec_field == 0:
#			child_row = opp_record.append("opp_stage", {})
#			child_row.stage_name = row.name
#			child_row.opportunity_purpose = row.opportunity_purpose
#			child_row.buying_status = row.buying_status
#			child_row.closing_date = row.closing_date
#			child_row.stage = row.stage
#			child_row.value = row.value
#			child_row.competition_status = row.competition_status
#			child_row.support_needed = row.support_needed
#
#		opp_record.save()
#		frappe.db.commit()	

		
	return

				
			

def set_missing_values(source, target_doc):
	target_doc.run_method("set_missing_values")
	target_doc.run_method("calculate_taxes_and_totals")


@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	boq_record = frappe.get_doc("Bill of Quantity", source_name)
	set_bom_level(boq_record)
	get_assembly_price(source_name)
	
	company = boq_record.company

	boq_record_items = frappe.db.sql("""select boqi.item_code as boq_item, boqi.immediate_parent_item, boq.customer as customer, boqi.qty as qty, boqi.sub_assembly_price as amount, boqi.markup as markup, boqi.print_in_quotation as piq, boqi.list_in_boq as list_in_boq, boqi.next_exploded as next_exploded from `tabBill of Quantity` boq, `tabBill of Quantity Item` boqi where boqi.parent = %s and boq.name = boqi.parent and boqi.print_in_quotation = '1'""" , (boq_record.name), as_dict=1)

	if boq_record_items:
		newJson = {
				"company": company,
				"doctype": "Quotation",
				"customer": boq_record.customer,
				"boq": source_name,
				"items": [
				]
				}
	
		for record in boq_record_items:
			item = record.boq_item
			qty = record.qty
			piq = record.piq
	 		lib = record.list_in_boq
			next_exploded = record.next_exploded
			markup = record.markup
			if item:
				item_record = frappe.get_doc("Item", item)

				innerJson =	{
					"doctype": "Quotation Item",
					"item_code": item,
					"description": item_record.description,
					"uom": item_record.stock_uom,
					"qty": qty,
					"rate": record.amount,
					"display_in_quotation": piq,
					"list_in_boq": lib,
					"next_exploded": next_exploded,
					"grouping": record.immediate_parent_item

					}
		
				newJson["items"].append(innerJson)

		doc = frappe.new_doc("Quotation")
		doc.update(newJson)
		doc.save()
		frappe.db.commit()
		docname = doc.name
		frappe.msgprint(_("Quotation Created - " + docname))
			
	else:	
		boq_main_item = frappe.db.sql("""select boq.item as boq_item, boq.customer as customer from `tabBill of Quantity` boq where boq.name = %s""" , (boq_record.name), as_dict=1)

		if boq_main_item:
			newJson = {
				"company": company,
				"doctype": "Quotation",
				"customer": boq_record.customer,
				"boq": source_name,
				"items": [
				]
			}
	
			tot_ass_price = flt(frappe.db.sql("""select sum(sub_assembly_price)
				from `tabBill of Quantity Item` boqi
				where boqi.parent=%s""",
				(boq_record.name))[0][0])
			if tot_ass_price == 0:
				
				tot_ass_price = flt(frappe.db.sql("""select sum(selling_price * qty)
				from `tabBill of Quantity Item` boqi
				where boqi.parent=%s""",
				(boq_record.name))[0][0])
			for record in boq_main_item:
				item = record.boq_item
				qty = 1
				piq = 1
				lib = 1

				if item:
					item_record = frappe.get_doc("Item", item)

					innerJson =	{
						"doctype": "Quotation Item",
						"item_code": item,
						"description": item_record.description,
						"uom": item_record.stock_uom,
						"qty": qty,
						"rate": tot_ass_price,
						"display_in_quotation": piq,
						"list_in_boq": lib,
#						"next_exploded": next_exploded,
#						"grouping": record.immediate_parent_item
	
						}
		
					newJson["items"].append(innerJson)

			doc = frappe.new_doc("Quotation")
			doc.update(newJson)
			doc.save()
			frappe.db.commit()
			docname = doc.name
			frappe.msgprint(_("Quotation Created - " + docname))

					
	

@frappe.whitelist()
def make_bom(source_name, target_doc=None):
	boq_record = frappe.get_doc("Bill of Quantity", source_name)
	company = boq_record.company
	max_bom_level = frappe.db.sql("""select max(bom_level) from `tabBill of Quantity Item` boqi where boqi.parent = %s""", (boq_record.name))
	x = 0
#	if max_bom_level > 0:
	if max_bom_level[0][0] is None or max_bom_level[0][0] is "":
		frappe.msgprint(_("Please create Quotation first"))	
		return	
	else:

		bom_level = int(max_bom_level[0][0])
		
#	else:
#		bom_level = 0

	if bom_level == 0:
		boq_record_items = frappe.db.sql("""select distinct boqi.immediate_parent_item as bom_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.bom_level = 0 order by boqi.immediate_parent_item""" , (boq_record.name), as_dict=1)

		if boq_record_items:
						
			for boq_record_item in boq_record_items:
				bom_main_item = boq_record_item.bom_item
				bom_qty = 1

				boq_record_bom_items = frappe.db.sql("""select boqi.item_code as qi_item, boqi.qty as qty, boqi.part_of_despatch_list as pod from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s and boqi.bom_level = 0 order by boqi.item_code""" , (boq_record.name, bom_main_item), as_dict=1)
				if boq_record_bom_items:
					
					newJson = {
					"company": company,
					"doctype": "BOM",
					"item": bom_main_item,
					"quantity": bom_qty,
					"items": [
					]
					}
					
					for record in boq_record_bom_items:
						item = record.qi_item
						qty = record.qty
						pod_list = record.pod

						if item:
							item_record = frappe.get_doc("Item", item)
		
							innerJson =	{
								"doctype": "BOM Item",
								"item_code": item,
								"description": item_record.description,
								"uom": item_record.stock_uom,
								"stock_uom": item_record.stock_uom,
								"qty": qty,
								"part_of_despatch_list": pod_list
								}
		
							newJson["items"].append(innerJson)

					doc = frappe.new_doc("BOM")
					doc.update(newJson)
					doc.save()
					frappe.db.commit()
					doc.submit()
					docname = doc.name
					frappe.msgprint(_("BOM Created - " + docname))

				else:
					frappe.msgprint(_("There are no BOM Items present in the quotation. Could not create a BOM for this Item."))

	else:
		for x in xrange(bom_level + 1):
			boq_record_items = frappe.db.sql("""select distinct boqi.immediate_parent_item as bom_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.bom_level = %s order by boqi.immediate_parent_item""" , (boq_record.name, x), as_dict=1)

			if boq_record_items:
						
				for boq_record_item in boq_record_items:
					bom_main_item = boq_record_item.bom_item
					bom_qty = 1

					boq_record_bom_items = frappe.db.sql("""select boqi.item_code as qi_item, boqi.qty as qty, boqi.part_of_despatch_list as pod from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s and boqi.bom_level = %s order by boqi.item_code""" , (boq_record.name, bom_main_item, x), as_dict=1)
			
					if boq_record_bom_items:
					
						newJson = {
						"company": company,
						"doctype": "BOM",
						"item": bom_main_item,
						"quantity": bom_qty,
						"items": [
						]
						}
					
						for record in boq_record_bom_items:
							item = record.qi_item
							qty = record.qty
							pod_list = record.pod

							if item:
								item_record = frappe.get_doc("Item", item)
		
								innerJson =	{
									"doctype": "BOM Item",
									"item_code": item,
									"description": item_record.description,
									"uom": item_record.stock_uom,
									"stock_uom": item_record.stock_uom,
									"qty": qty,
									"part_of_despatch_list": pod_list
								
				
									}
		
								newJson["items"].append(innerJson)

						doc = frappe.new_doc("BOM")
						doc.update(newJson)
						doc.save()
						frappe.db.commit()
						doc.submit()
						docname = doc.name
						frappe.msgprint(_("BOM Created - " + docname))
	
					else:
						frappe.msgprint(_("There are no BOM Items present in the quotation. Could not create a BOM for this Item."))



def set_bom_level(boq_record):
	boq_record_items = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s""" , (boq_record.name, boq_record.item), as_dict=1)

	if boq_record_items:
		for row in boq_record_items:

			bom_record_level1 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s""" , (boq_record.name, row.item_code), as_dict=1)

			if bom_record_level1:
				for record in bom_record_level1:
					frappe.db.sql("""update `tabBill of Quantity Item` boqi set boqi.bom_level = "1" where boqi.parent = %s and boqi.immediate_parent_item = %s""", (boq_record.name, boq_record.item))
			else:

				frappe.db.sql("""update `tabBill of Quantity Item` boqi set boqi.bom_level = "0" where boqi.parent = %s and boqi.item_code = %s""", (boq_record.name, row.item_code))


	boq_record_items2 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.bom_level = 1""" , (boq_record.name), as_dict=1)
	if boq_record_items2:
		for row in boq_record_items2:
			bom_record_level2 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s""" , (boq_record.name, row.item_code), as_dict=1)
			for record in bom_record_level2:
				frappe.db.sql("""update `tabBill of Quantity Item` boqi set boqi.bom_level = "2" where boqi.parent = %s and boqi.item_code = %s and boqi.immediate_parent_item = %s""", (boq_record.name, record.item_code, record.immediate_parent_item))

	boq_record_items3 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.bom_level = 2""" , (boq_record.name), as_dict=1)
	if boq_record_items3:
		for row in boq_record_items3:
			bom_record_level3 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s""" , (boq_record.name, row.item_code), as_dict=1)
			for record in bom_record_level3:
				frappe.db.sql("""update `tabBill of Quantity Item` boqi set boqi.bom_level = "3" where boqi.parent = %s and boqi.item_code = %s and boqi.immediate_parent_item = %s""", (boq_record.name, record.item_code, record.immediate_parent_item))

	boq_record_items4 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.bom_level = 3""" , (boq_record.name), as_dict=1)
	if boq_record_items4:
		for row in boq_record_items4:
			bom_record_level4 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s""" , (boq_record.name, row.item_code), as_dict=1)
			for record in bom_record_level4:
				frappe.db.sql("""update `tabBill of Quantity Item` boqi set boqi.bom_level = "4" where boqi.parent = %s and boqi.item_code = %s and boqi.immediate_parent_item = %s""", (boq_record.name, record.item_code, record.immediate_parent_item))

	boq_record_items5 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.bom_level = 4""" , (boq_record.name), as_dict=1)
	if boq_record_items5:
		for row in boq_record_items5:
			bom_record_level5 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s""" , (boq_record.name, row.item_code), as_dict=1)
			for record in bom_record_level5:
				frappe.db.sql("""update `tabBill of Quantity Item` boqi set boqi.bom_level = "5" where boqi.parent = %s and boqi.item_code = %s and boqi.immediate_parent_item = %s""", (boq_record.name, record.item_code, record.immediate_parent_item))

	boq_record_items6 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.bom_level = 5""" , (boq_record.name), as_dict=1)
	if boq_record_items6:
		for row in boq_record_items6:
			bom_record_level6 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s""" , (boq_record.name, row.item_code), as_dict=1)
			for record in bom_record_level6:
				frappe.db.sql("""update `tabBill of Quantity Item` boqi set boqi.bom_level = "6" where boqi.parent = %s and boqi.item_code = %s and boqi.immediate_parent_item = %s""", (boq_record.name, record.item_code, record.immediate_parent_item))
							

	boq_record_items7 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.bom_level = 6""" , (boq_record.name), as_dict=1)
	if boq_record_items7:
		for row in boq_record_items7:
			bom_record_level7 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s""" , (boq_record.name, row.item_code), as_dict=1)
			for record in bom_record_level7:
				frappe.db.sql("""update `tabBill of Quantity Item` boqi set boqi.bom_level = "7" where boqi.parent = %s and boqi.item_code = %s and boqi.immediate_parent_item = %s""", (boq_record.name, record.item_code, record.immediate_parent_item))

	boq_record_items8 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.bom_level = 7""" , (boq_record.name), as_dict=1)
	if boq_record_items8:
		for row in boq_record_items8:
			bom_record_level8 = frappe.db.sql("""select boqi.item_code, boqi.immediate_parent_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s""" , (boq_record.name, row.item_code), as_dict=1)
			for record in bom_record_level8:
				frappe.db.sql("""update `tabBill of Quantity Item` boqi set boqi.bom_level = "8" where boqi.parent = %s and boqi.item_code = %s and boqi.immediate_parent_item = %s""", (boq_record.name, record.item_code, record.immediate_parent_item))

@frappe.whitelist()
def make_cust_project(source_name, target_doc=None):
	global alloc_whse
	def postprocess(source, doc):
		doc.project_type = "External"
		sales_record = frappe.get_doc("Sales Order", source_name)
		customer = sales_record.customer
		doc.project_name = customer + "-" + source_name[-5:]
 		doc.production_bench = get_free_workbenches()

		if doc.production_bench:
			pass
		else:
			frappe.msgprint(_("There is no free production bench available. Please allocate manually"))

	doc = get_mapped_doc("Sales Order", source_name, {
		"Sales Order": {
			"doctype": "Project",
			"validation": {
				"docstatus": ["=", 1]
			},
			"field_map":{
				"name" : "sales_order",
				"base_grand_total" : "estimated_costing",
			}
		},
		"Sales Order Item": {
			"doctype": "Project Task",
			"field_map": {
				"description": "title",
			},
		}
	}, target_doc, postprocess)

	return doc

@frappe.whitelist()
def get_free_workbenches():

	workbench_warehouses = frappe.db.sql("""select name from `tabWarehouse` where parent_warehouse = "Production Benches - PISPL" order by name""", as_dict=1)

	for whse_record in workbench_warehouses:
		alloc_whse = frappe.db.sql("""select is_active from `tabProject` where production_bench = %s and is_active = "Yes" order by name""", (whse_record["name"]), as_dict=1)
		if alloc_whse:
			pass
		else:
			return whse_record["name"]


@frappe.whitelist()
def get_price(item, price_list):
	item_price_list = frappe.db.sql("""select name as price, price_list_rate as item_price from `tabItem Price` where price_list = %s and item_code = %s""", (price_list, item), as_dict = 1)
	if item_price_list:
#		return item_price_list[0]["item_price"]
		return item_price_list[0]["price"], item_price_list[0]["item_price"]
		
	else:	
		return 0



@frappe.whitelist()
def get_contact(customer):
	contact = frappe.db.sql("""select con.name from `tabContact` con, `tabDynamic Link` dy where dy.link_name = %s and dy.parent = con.name""", (customer))
	
	return contact


@frappe.whitelist()
def get_address(customer):
	address = frappe.db.sql("""select ad.name from `tabAddress` ad, `tabDynamic Link` dy where dy.link_name = %s and dy.parent = ad.name""", (customer))

	return address
	

@frappe.whitelist()
def get_assembly_price(frm):
	boq_record = frappe.get_doc("Bill of Quantity", frm)
	company = boq_record.company
	max_bom_level = frappe.db.sql("""select max(bom_level) from `tabBill of Quantity Item` where parent = %s""", frm)

	x = 1
	sub_ass_price = 0
	markup_per = 1
	bom_level = int(max_bom_level[0][0])
	for x in xrange(bom_level, 0, -1):

		boq_record_items = frappe.db.sql("""select distinct boqi.immediate_parent_item as bom_item from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.bom_level = %s order by boqi.immediate_parent_item""" , (boq_record.name, x), as_dict=1)

		if boq_record_items:
			
			for boq_record_item in boq_record_items:
				bom_main_item = boq_record_item.bom_item
				markup_rec = frappe.db.sql("""select boqi.markup as markup, boqi.discount as discount, boqi.qty as qty from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.item_code = %s""" , (boq_record.name, bom_main_item))
#				markup = markup_rec.markup
				if markup_rec:
					markup = markup_rec[0][0]
					discount = markup_rec[0][1]
					bom_main_qty = markup_rec[0][2]
				else:
					markup = 0
					bom_main_qty = 1
				bom_qty = 1
				sub_ass_price = 0

				boq_record_bom_items = frappe.db.sql("""select boqi.item_code as qi_item, boqi.qty as qty, boqi.selling_price as selling_price, boqi.sub_assembly_price as sap from `tabBill of Quantity Item` boqi where boqi.parent = %s and boqi.immediate_parent_item = %s and boqi.bom_level = %s order by boqi.item_code""" , (boq_record.name, bom_main_item, x), as_dict=1)
				if boq_record_bom_items:
										
					for record in boq_record_bom_items:
						item = record.qi_item
						qty = record.qty
						selling_price = record.selling_price
						sap = flt(record.sap)
						if sap != 0.0:

							sub_ass_price = sub_ass_price + flt(sap * qty)

						else:

							sub_ass_price = sub_ass_price + (selling_price * qty)

				markup_per = flt(markup/100) + 1
				disc_per = 1 - flt(discount/100)
				sub_ass_price = (sub_ass_price * markup_per * disc_per)

				frappe.db.sql("""update `tabBill of Quantity Item` boqi set boqi.sub_assembly_price = %s where boqi.parent = %s and boqi.item_code = %s""", (sub_ass_price, boq_record.name, bom_main_item))
						


@frappe.whitelist()
def make_opp_quotation(source_name, target_doc=None):
	frappe.throw(_("Inside Api - Opportunity to Quotation"))
	def set_missing_values(source, target):
		from erpnext.controllers.accounts_controller import get_default_taxes_and_charges
		quotation = frappe.get_doc(target)

		company_currency = frappe.db.get_value("Company", quotation.company, "default_currency")
		party_account_currency = get_party_account_currency("Customer", quotation.customer,
			quotation.company) if quotation.customer else company_currency

		quotation.currency = party_account_currency or company_currency

		if company_currency == quotation.currency:
			exchange_rate = 1
		else:
			exchange_rate = get_exchange_rate(quotation.currency, company_currency,
				quotation.transaction_date)

		quotation.conversion_rate = exchange_rate

		# get default taxes
		taxes = get_default_taxes_and_charges("Sales Taxes and Charges Template", company=quotation.company)
		if taxes.get('taxes'):
			quotation.update(taxes)

		quotation.run_method("set_missing_values")
		quotation.run_method("calculate_taxes_and_totals")
		if not source.with_items:
			quotation.opportunity = source.name

	doclist = get_mapped_doc("Opportunity", source_name, {
		"Opportunity": {
			"doctype": "Quotation",
			"field_map": {
				"enquiry_from": "quotation_to",
				"opportunity_type": "order_type",
				"name": "enq_no",
			}
		},
		"Opportunity Item": {
			"doctype": "Quotation Item",
			"field_map": {
				"parent": "prevdoc_docname",
				"parenttype": "prevdoc_doctype",
				"uom": "stock_uom"
			},
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)

	return doclist

@frappe.whitelist()
def get_item_price_details(item_code):
	
	item_details = []
	supplier_details = []
	last_3Days_Details = frappe.db.sql("""select rate,parent from `tabPurchase Order Item` as tpoi where item_code = %s and DATE(creation) > (NOW() - INTERVAL 3 DAY) and ((select status from `tabPurchase Order` where name=tpoi.parent) not in ('Draft','Cancelled')) order by creation desc limit 3""", (item_code), as_dict=1)
	#print "############-length of last_3Days_Details[0]['parent']::", (last_3Days_Details)
	i=0
	for po_Number in last_3Days_Details:
		last_3Days_po_Number = last_3Days_Details[i]['parent']
		last_3Days_supplier = frappe.db.sql("""select supplier from `tabPurchase Order` where name = %s and DATE(creation) > (NOW() - INTERVAL 3 DAY) order by creation desc limit 3""", last_3Days_po_Number, as_dict=1)
		supplier_details.extend(last_3Days_supplier)
		i = i + 1
	#print "###-supplier_details::", supplier_details
	max_last_180Days_Details = frappe.db.sql("""select parent,rate as max_price_rate from (select parent,rate from `tabPurchase Order Item`  as tpoi where item_code = %s and DATE(creation) > (NOW() - INTERVAL 180 DAY) and ((select status from `tabPurchase Order` where name=tpoi.parent) not in ('Draft','Cancelled')) order by rate desc limit 1) t1""", (item_code), as_dict=1)
	#print "#######-max_last_180Days_Details::", max_last_180Days_Details
	if len(max_last_180Days_Details)!=0:
		max_last_180Days_po_Number = max_last_180Days_Details[0]['parent']
		max_last_180Days_supplier = frappe.db.sql("""select supplier from `tabPurchase Order` where name = %s""", max_last_180Days_po_Number, as_dict=1)
		max_last_180Days_Details.extend(max_last_180Days_supplier)

	min_last_180Days_Details = frappe.db.sql("""select parent,rate as min_price_rate from (select parent,rate from `tabPurchase Order Item`  as tpoi where item_code = %s and DATE(creation) > (NOW() - INTERVAL 180 DAY) and ((select status from `tabPurchase Order` where name=tpoi.parent) not in ('Draft','Cancelled')) order by rate asc limit 1) t1""", (item_code), as_dict=1)
	if len(min_last_180Days_Details)!=0:
		#print "#######-min_last_180Days_Details::", min_last_180Days_Details
		min_last_180Days_po_Number = min_last_180Days_Details[0]['parent']
		min_last_180Days_supplier = frappe.db.sql("""select supplier from `tabPurchase Order` where name = %s""", min_last_180Days_po_Number, as_dict=1)
		min_last_180Days_Details.extend(min_last_180Days_supplier)

	last_180Days_Avg_Price = frappe.db.sql("""select avg(rate) as avg_price from `tabPurchase Order Item` as tpoi where item_code = %s and DATE(creation) > (NOW() - INTERVAL 180 DAY) and ((select status from `tabPurchase Order` where name=tpoi.parent) not in ('Draft','Cancelled'))""", (item_code), as_dict=1)

	#last_3Days_Details.extend(last_3Days_supplier)
	item_details.append(last_3Days_Details)
	item_details.append(max_last_180Days_Details)
	item_details.append(min_last_180Days_Details)
	item_details.append(last_180Days_Avg_Price)
	item_details.append(supplier_details)
	print "###############-item_details::", item_details
	return item_details


@frappe.whitelist()
def calculate_overtime_and_food(employee, start_date, end_date):
#	overtime_fa_amount = frappe.db.sql("""select sum(ofe.overtime_amount) as overtime, sum(food_allowance_amount) as food_allowance, sum(attendance_bonus) as attendance_bonus
#			from `tabOvertime and Other Allowances` ofa, `tabOvertime and Other Allowances Employees` ofe where ofe.employee = %s and ofa.from_date >= %s and ofa.to_date <= %s and ofe.parent = ofa.name and ofa.docstatus = 1""",
#			(employee, start_date, end_date), as_dict=1)

	overtime_fa_amount = frappe.db.sql("""select sum(ofe.overtime_hours) as overtime_hours, sum(ofe.overtime_amount) as overtime, sum(food_allowance_amount) as food_allowance, sum(attendance_bonus) as attendance_bonus
			from `tabOvertime and Other Allowances` ofa, `tabOvertime and Other Allowances Employees` ofe where ofe.employee = %s and ofa.from_date >= %s and ofa.to_date <= %s and ofe.parent = ofa.name and ofa.docstatus = 1""",
			(employee, start_date, end_date), as_dict=1)

	return overtime_fa_amount


@frappe.whitelist()
def get_uom_list(item_code):
	records = frappe.db.sql("""select t2.uom as uom from `tabUOM Conversion Detail` t2 where t2.parent = %s""", (item_code))

	if records:
#		frappe.msgprint(_(records[0].warehouse))
#		return records[0].warehouse
		return records
	else:
		return

@frappe.whitelist()
def get_user_role():
	userrole = frappe.db.get_value("User",{"name":frappe.session.user},"role_profile_name")
	if userrole:
		return userrole	
	else:
		return 1

@frappe.whitelist()
def get_user_role_status(approval_a, dt):
	frappe.msgprint(_("Inside api"))
	frappe.msgprint(_(approval_a))
	role_status = ""
	userrole = frappe.db.get_value("User",{"name":frappe.session.user},"role_profile_name")
	frappe.msgprint(_(userrole))
	if userrole:
		if approval_a == "Rejected":
			role_status = "Rejected"
			return role_status
		else:
			workflow_records = frappe.db.sql("""select at.approval_level, at.approval_role, at.approval_status from `tabApproval Master` am, `tabApproval Transition` at where at.parent = am.name and am.document_type = %s""", (dt), as_dict = 1)
			if workflow_records:
				for wfw in workflow_records:
					if userrole == wfw.approval_role:
						if wfw.approval_status:
							role_status = wfw.approval_status
						else:
							role_status = "Approved by " + userrole

				if role_status:
					frappe.msgprint(_(role_status))
					return role_status
				else:
					return 0
			else:
				frappe.msgprint(_("There are no Approval workflow records set for doctype: " + dt))	
				return 0
	else:
		return 0

@frappe.whitelist()
def delete_rarb(warehouse):
	upd_old_rarb_det = frappe.db.sql("""select name from `tabRARB Detail` where warehouse = %s and active = 1""", warehouse, as_dict=1)
	whs_rec = frappe.db.sql("""select version from `tabWarehouse` where name = %s""", warehouse)
	frappe.msgprint(_(whs_rec[0]))
	ver = whs_rec[0][0] + 1
	ver = str(ver).zfill(3)
	curr_date = utils.today()
	if upd_old_rarb_det:
		for rec in upd_old_rarb_det:
			rarb_rec = frappe.get_doc("RARB Detail", rec.name)
			sys_id = rec.name + "-" + ver
			newJson = {
				"system_id": sys_id,
				"doctype": "RARB Detail",
				"next_level_rarb": rarb_rec.next_level_rarb,
				"next_level_rarb_number": rarb_rec.next_level_rarb_number,
				"warehouse": rarb_rec.warehouse,
				"item": rarb_rec.item,
				"attribute_1": rarb_rec.attribute_1,
				"attribute_2": rarb_rec.attribute_2,
				"attribute_3": rarb_rec.attribute_3,
				"length": rarb_rec.length,
				"width": rarb_rec.width,
				"height": rarb_rec.height,
				"max_permissible_weight": rarb_rec.max_permissible_weight,
				"reqd_to_select_bin": rarb_rec.reqd_to_select_bin,
				"active": 0
				}
			doc = frappe.new_doc("RARB Detail")
			doc.update(newJson)
			doc.save()
			frappe.db.commit()

	frappe.db.sql("""update `tabWarehouse` set version = %s where name = %s""", (ver, warehouse))
	frappe.db.sql("""delete from `tabRARB Locations` where parent in (select name from `tabRARB` where warehouse = %s and active = 1)""", warehouse, as_dict=1)
	frappe.db.sql("""delete from `tabRARB Detail` where warehouse = %s and active = 1""", warehouse, as_dict=1)
	frappe.db.sql("""delete from `tabRARB` where warehouse = %s and active = 1""", warehouse, as_dict=1)

		
	
@frappe.whitelist()
def validate_rarb(warehouse):
	frappe.msgprint(_("Inside Validate RARB"))
	exists = ""
	rarb_rec = frappe.db.sql("""Select name from `tabRARB` where name = %s""", warehouse, as_dict=1)
	if rarb_rec:
		exists = 1
	else:
		exists = 0
	return exists

@frappe.whitelist()
def generate_rarb(warehouse, rooms, aisle, rack, bin_no):
	room = int(rooms) + 1
	ais = int(aisle) + 1
	rac = int(rack) + 1
	bin_n = int(bin_no) + 1
	newJson = {
		"system_id": warehouse,
		"rarb_id": warehouse,
		"doctype": "RARB Detail",
		"next_level_rarb": "Room",
		"next_level_rarb_number": room,
		"warehouse": warehouse,
		"active": 1
		}
	doc = frappe.new_doc("RARB Detail")
	doc.update(newJson)
	doc.save()
	frappe.db.commit()
	newJson_wh = {
			"higher_rarb": warehouse,
			"warehouse": warehouse,
			"active": 1,
				"rarb_locations": [
				]
			}
	
	for w in xrange(1, room):
		room_id = warehouse + "-Room-" + str(w)
		rarb_room = "Room-" + str(w)
		newJson = {
			"system_id": room_id,
			"rarb_id": rarb_room,
			"doctype": "RARB Detail",
			"next_level_rarb": "Aisle",
			"next_level_rarb_number": aisle,
			"warehouse": warehouse,
			"active": 1
			}
		innerJson_wh =	{
				"rarb_location": room_id

				}
		
		newJson_wh["rarb_locations"].append(innerJson_wh)
		doc = frappe.new_doc("RARB Detail")
		doc.update(newJson)
		doc.save()
		frappe.db.commit()
		newJson_rm = {
			"higher_rarb": room_id,
			"warehouse": warehouse,
			"active": 1,
				"rarb_locations": [
				]
			}

		for x in xrange(1, ais):
			aisle_id = warehouse + "-Aisle-" + str(w) + "-" + str(x)
			rarb_aisle = "Aisle-" + str(w) + "-" + str(x)
			newJson = {
				"system_id": aisle_id,
				"rarb_id": rarb_aisle,
				"doctype": "RARB Detail",
				"next_level_rarb": "Rack",
				"next_level_rarb_number": rack,
				"warehouse": warehouse,
				"active": 1

				}
			innerJson_rm =	{
				"rarb_location": aisle_id

				}
			newJson_rm["rarb_locations"].append(innerJson_rm)

			doc = frappe.new_doc("RARB Detail")
			doc.update(newJson)
			doc.save()
			frappe.db.commit()
			newJson_ai = {
			"higher_rarb": aisle_id,
			"warehouse": warehouse,
			"active": 1,
				"rarb_locations": [
				]
			}

			for y in xrange(1, rac):
				rac_id = warehouse + "-Rack-" + str(w) + "-" + str(x)+ "-" + str(y)
				rarb_rack = "Rack-" + str(w) + "-" + str(x)+ "-" + str(y)
				newJson = {
					"system_id": rac_id,
					"rarb_id": rarb_rack,
					"doctype": "RARB Detail",
					"next_level_rarb": "Bin",
					"next_level_rarb_number": bin_no,
					"warehouse": warehouse,
					"active": 1

				}
				innerJson_ai =	{
					"rarb_location": rac_id

					}
				newJson_ai["rarb_locations"].append(innerJson_ai)

				doc = frappe.new_doc("RARB Detail")
				doc.update(newJson)
				doc.save()
				frappe.db.commit()
				newJson_rac = {
					"higher_rarb": rac_id,
					"warehouse": warehouse,
					"active": 1,
					"rarb_locations": [
						]
					}
				for z in xrange(1, bin_n):
					bin_id = warehouse + "-Bin-" + str(w) + "-" + str(x)+ "-" + str(y)+ "-" + str(z)
					rarb_bin = "Bin-" + str(w) + "-" + str(x)+ "-" + str(y)+ "-" + str(z)
					newJson = {
						"system_id": bin_id,
						"rarb_id": rarb_bin,
						"doctype": "RARB Detail",
						"warehouse": warehouse,
						"active": 1
						}
					innerJson_rac =	{
						"rarb_location": bin_id

						}
					newJson_rac["rarb_locations"].append(innerJson_rac)

					doc = frappe.new_doc("RARB Detail")
					doc.update(newJson)
					doc.save()
					frappe.db.commit()

				doc_rac = frappe.new_doc("RARB")
				doc_rac.update(newJson_rac)
				doc_rac.save()
				frappe.db.commit()

			doc_ai = frappe.new_doc("RARB")
			doc_ai.update(newJson_ai)
			doc_ai.save()
			frappe.db.commit()

		doc_rm = frappe.new_doc("RARB")
		doc_rm.update(newJson_rm)
		doc_rm.save()
		frappe.db.commit()

	doc_wh = frappe.new_doc("RARB")
	doc_wh.update(newJson_wh)
	doc_wh.save()
	frappe.db.commit()
	frappe.throw(_("RARBs created"))
	return

@frappe.whitelist()
def make_po_in_draft(purchase_items,purchase_taxes,purchase_order_details,payment_schedule):
	name = ""
	title = ""
	owner = ""
	taxes_and_charges = ""
	company = ""
	supplier = ""
	stopped_po="" 
	schedule_date = ""
	stock_req = ""
	stock_req_id = ""
	busyvoucherno = ""
	item_lines_to_print = 0
	apply_discount_on = ""
	project = ""
	additional_discount_percentage = 0
	remark = ""
	material_req = ""
	payment_terms = ""
	due_date = ""
	payment_term = ""
	return_doc = ""
	inner_json_for_items = ""
	inner_json_for_taxes = ""
	required_date = datetime.now()
	purchase_order_details = ast.literal_eval(purchase_order_details) 
	purchase_taxes = ast.literal_eval(purchase_taxes) 
	purchase_items = ast.literal_eval(purchase_items)
	payment_schedule = ast.literal_eval(payment_schedule)
	for data in purchase_order_details:
		title = data["title"]
		owner = data["owner"]
		taxes_and_charges = data["taxes_and_charges"]
		company = data["company"]
		supplier = data["supplier"]
		stopped_po = data["name"] 
		schedule_date = data["schedule_date"]
		stock_req =  data["stock_req"]
		busyvoucherno =  data["busyvoucherno"]
		item_lines_to_print = data["item_lines_to_print"]
		additional_discount_percentage = data["additional_discount_percentage"]
		project = data["project"]
		remark = data["remark"]
		material_req = data["material_req"]
		payment_terms = data["payment_terms_template"]
		apply_discount_on = data["apply_discount_on"]
		name = data["name"]
	for data in payment_schedule:
		due_date = data['due_date']
	
	outer_json = {
		"doctype": "Purchase Order",
		"title" : title,
		"creation" : required_date,
		"docstatus" : 0,
		"owner" : owner,
		"taxes_and_charges" :taxes_and_charges,
		"company" : company,
		"due_date" : due_date,
		"supplier" : supplier,
		"stopped_po":stopped_po,
		"schedule_date" :schedule_date,
		"stock_req" : stock_req,
		"stock_requisition_id" : stock_req_id,
		"additional_discount_percentage" :additional_discount_percentage,
		"busyvoucherno" : busyvoucherno,
		"item_lines_to_print" : item_lines_to_print,
		"project" : project,
		"tracking_no" : remark,
		"material_request" : material_req,
		"payment_terms_template":payment_terms,
		"apply_discount_on" :apply_discount_on,
		"items":[],
		"taxes":[]
		}

	for data in purchase_items:
		item_code = data['item_code']
		received_qty = data['received_qty']
		target_warehouse = data['warehouse']
		last_purchase_price = data["last_purchase_rate"]
		parentfield = data["parentfield"]
		qty_as_per_stock_uom = data['stock_qty']
		rate = data['rate']
		pending_qty = qty_as_per_stock_uom-received_qty
		pending = hash(round(pending_qty, 1))
		if pending > 0:
			inner_json_for_items = {
				"item_code": item_code,
				"doctype": "Purchase Order Item",
				"qty": pending_qty,
				"schedule_date": required_date,
				"last_purchase_price" : last_purchase_price,
				"parentfield" : parentfield,
				"warehouse":target_warehouse,
				"qty_as_per_stock_uom":qty_as_per_stock_uom,
				"rate":rate
			}
			outer_json["items"].append(inner_json_for_items)
	for data in purchase_taxes:
		charge_type = data['charge_type']
		account_head = data['account_head']
		rate = data['rate']
		tax_amount = data["tax_amount"]
		description = data["description"]
			
		inner_json_for_taxes = {
			"charge_type" : charge_type,
			"account_head":account_head,
			"rate":rate,
			"tax_amount": tax_amount,
			"description" :description,
		}

		if "row_id" in data:
			row_id = data["row_id"]
			if row_id is not None:
				inner_json_for_taxes["row_id"] = row_id
		outer_json["taxes"].append(inner_json_for_taxes)
	doc = frappe.new_doc("Purchase Order")
	doc.update(outer_json)	
	doc.save()
	return_doc = doc.doctype
	frappe.msgprint("Purchase Order is Created  :  "+doc.name)
	po_doc = frappe.get_doc("Purchase Order", name)
	po_doc.set_status(update = True , status = "Closed")
	po_doc.save()	
	return_doc = po_doc.doctype
	if return_doc:
		return return_doc 

@frappe.whitelist()
def make_sreq(stock_requisition_list,company,stopped_po):
	required_date = datetime.now()
	return_doc = ""
	innerJson = " "
	sreq_items = json.loads(stock_requisition_list)
	sreq_items = json.dumps(sreq_items)
	sreq_items_list = ast.literal_eval(sreq_items)
	outerJson = {
			"doctype": "Stock Requisition",
			"company": company,
			"title": "Purchase",
			"workflow_state": "Pending Approval",
			"docstatus": 0,
			"purpose": "Purchase",
			"requested_by": stopped_po,
			"items": []
			}
	for data in sreq_items_list:
		innerJson = {
			"doctype": "Stock Requisition Item",
			"item_code": data['item_code'],
			"qty": data['qty'],
			"schedule_date": required_date,
			"warehouse":data['warehouse']
		}
		outerJson["items"].append(innerJson)
	doc = frappe.new_doc("Stock Requisition")
	doc.update(outerJson)
	doc.save()

@frappe.whitelist()
def fetch_stopped_po_items(stopped_po):
	items = []
	items = frappe.db.sql("""select item_code,qty,rate,price_list_rate,received_qty from `tabPurchase Order Item` where parent=%s""", 					(stopped_po), as_dict = 1)
	if items:
		return items
	else:
		return items

@frappe.whitelist()
def for_item_code():
	item_code_details = frappe.db.sql("""select name,current from `tabSeries` where name='FI-'""",as_dict=1)
	return item_code_details


@frappe.whitelist()
def series_update(current_num,name):
	updated = frappe.db.sql("""UPDATE `tabSeries` SET current = '"""+current_num+"""' where name = %s""",(name),as_dict=1)
	return updated

@frappe.whitelist()
def user_details(user):
	user_data = frappe.db.sql("""select role from `tabHas Role` where parent = '"""+user+"""' AND role ='Sales Prospector' """,as_dict=1)
	return user_data

@frappe.whitelist()
def get_bom_list_for_so(item_code):
	records = frappe.db.sql("""select name  from `tabBOM` where item=%s and docstatus=1""", (item_code), as_dict=1)
	return records

##- Start of making .PRN file for Purchase Invoice Doc.
@frappe.whitelist()
def make_prnfile(invoice,ncopies,label):
	print "-------invoice-------------", invoice
	invoice_data = frappe.get_doc("Purchase Invoice", invoice)
	printer_details = frappe.get_doc("Label Printer", label)
	address = printer_details.address
	split_address = address.split("\n")
	items_list = invoice_data.items
	posting_date = invoice_data.posting_date
	date_of_import = posting_date.strftime("%m/%y")
	#file_path = os.path.expanduser('~') +'/ERPNext_PINV_PRN.PRN'

	fname = str(invoice) + "_" + str(posting_date) +".PRN"
	save_path = 'site1.local/private/files'
	file_name = os.path.join(save_path, fname)
	ferp = frappe.new_doc("File")
	ferp.file_name = fname
	ferp.folder = "Home/Labels"
	ferp.is_private = 1
	ferp.file_url = "/private/files/"+fname

	prn_file = open(file_name,"w+")
	
	for items in items_list:
		copies = 1
		qty = items.qty
		total_copies = int(qty) * int(ncopies)
		item_record = frappe.get_doc("Item", items.item_code)
		price_list = frappe.get_doc("Item Price", {"item_code": items.item_code, "price_list": "Standard Selling"}, "price_list_rate")

		for copies in xrange(total_copies):
			prn_file.write("<xpml><page quantity='0' pitch='50.8 mm'></xpml>G0\015" +"\n")
			prn_file.write("n\015"+"\n") 
			prn_file.write("M0500\015"+"\n") 
			prn_file.write("MT\015"+"\n") 
			prn_file.write("O0214\015"+"\n") 
			prn_file.write("V0\015"+"\n") 
			prn_file.write("t1\015"+"\n") 
			prn_file.write("Kf0070\015"+"\n") 
			prn_file.write("SG\015"+"\n") 
			prn_file.write("c0000\015"+"\n") 
			prn_file.write("e\015"+"\n") 
			prn_file.write("<xpml></page></xpml><xpml><page quantity='1' pitch='50.8 mm'></xpml>L\015"+"\n") 
			prn_file.write("D11\015"+"\n"+"H14\015"+"\n"+"PG\015"+"\n"+"PG\015"+"\n"+"SG\015"+"\n"+"ySPM\015"+"\n"+"A2\015"+"\n") 
			prn_file.write("1911C1001760021" + str(items.item_name)+"\015"+"\n") #product-name
			prn_file.write("4911C0801000013" + str(items.item_code)+"\015"+"\n") #Barcode
			prn_file.write("1e8404201270018C0201&E0$2" + str(items.item_code)+"\015"+"\n") #ProductCode
			#prn_file.write("1911C1001570260" + "Black"+"\n") #item-color
			#prn_file.write("1911C1001570260" + "L" +"\n") #item-size
			prn_file.write("1911C1001050019Month & Yr of Import" +"\015"+ "\n") 
			prn_file.write("1911C10010501600" + str(date_of_import) + "\015"+ "\n") 
			prn_file.write("1911C1200800019M.R.P." +"\015"+ "\n") 
			prn_file.write("1911C1200800105" + str(price_list.price_list_rate) +"\015"+"\n") #selling price
			prn_file.write("1911A0800670148Inclusive of all taxes" +"\015"+ "\n") 
			prn_file.write("1911A0800990227Qty" +"\015"+ "\n") 
			prn_file.write("1911A0800830227" + str(items.qty) + " " +str(items.stock_uom) +"\015"+ "\n") # Qty and UOM
			if len(split_address)!=0:
				if len(split_address) == 3:
					prn_file.write("1911C0800400012" + str(split_address[0]) +"\015"+ "\n") 
					prn_file.write("1911C08002500206,"+ str(split_address[1]) +"\015"+ "\n") 
					prn_file.write("1911C0800090005"+str(split_address[2]) +"\015"+ "\n") 
				else:
					prn_file.write("1911C0800400012" + str(split_address[0]) +"\015"+ "\n")
			prn_file.write("Q0001\015"+"\n") 
			prn_file.write("E\015"+"\n") 
			prn_file.write("<xpml></page></xpml><xpml><end/></xpml>\015"+"\n") 
	ferp.save()
	prn_file.close()
	frappe.msgprint(_("PRN File created - Please check File List to download the file"))
##- End of- making .PRN file for Purchase Invoice Doc.

## Start of- Set up an Auto E-Mail report to Supplier.
def send_mail_custom(recipient,content):
	frappe.sendmail(recipients=[recipient],
        sender="erptest@meritsystems.com",
        subject="Purchase Order Alert", content=content)

@frappe.whitelist()
def getPoData():
	send_email_check=frappe.db.get_single_value ('Stock Settings','send_daily_reminders_to_suppliers')
	if send_email_check:
		today_date = utils.today()
		day_name = datetime.datetime.strptime(today_date,'%Y-%m-%d').strftime('%A')

		if day_name == "Sunday":
			print "The mails are not send on sunday"
		elif day_name == "Saturday":
			one_day_after = add_days(utils.today(),1)
			two_days_after= add_days(utils.today(),2)
			request_doc=frappe.db.sql("""select  name from `tabPurchase Order` where schedule_date in (%s,%s) and docstatus=1""", (one_day_after,two_days_after),as_dict = 1)

			for doc in request_doc:
				po_doc=frappe.get_doc("Purchase Order",doc['name'])
				supplier_email=getSupplierEmail(po_doc.supplier)
				content = getSupplierContent(doc.name)
				send_mail_custom(supplier_email,content)
		else:
			request_doc=frappe.db.sql("""select  name from `tabPurchase Order` where schedule_date=%s and docstatus=1""",one_day_after,as_dict = 1) 
			for doc in request_doc:
				po_doc=frappe.get_doc("Purchase Order",doc['name'])
				supplier_email=getSupplierEmail(po_doc.supplier)
				content = getSupplierContent(doc.name)
				send_mail_custom(supplier_email,content)	
	else:
		pass

@frappe.whitelist()
def getSupplierEmail(supplier):
	supplier_doc=frappe.get_all("Contact",filters=[["Dynamic Link","link_doctype","=","Supplier"],["Dynamic Link","link_name","=",supplier]],fields=["email_id"])
	return supplier_doc[0].email_id
		

@frappe.whitelist()
def getSupplierContent(po_name):
	content = ""
	content ="<p> <h2>Following Items are need to be delivered for Purchase order :{0}</h2> </p><ol>".format(po_name)
	content+="<table border=2px > <tr> <th> Sr No</th> <th>Product Description</th> <th> Qty</th> <th>UOM</th> <th>Rate</th> <th>Amount<th> </tr>"

	po_items = frappe.db.sql("""select idx,description,qty,uom,rate,amount from `tabPurchase Order Item` where parent = %s order by idx """ , (po_name), as_dict=1)
	for po_item in po_items:
		content += "<tr> <td align='center'>{0}</td> <td align='center'>{1}</td> <td align='center'>{2}</td> <td align='center'>{3}</td> <td align='right'>{4}</td> <td align='right'>{5}</td> </tr>".format(po_item.idx,po_item.description, po_item.qty,po_item.uom,po_item.rate,po_item.amount)
	return content
## End of- Set up an Auto E-Mail report to Supplier

## Start of- Rounding and Charging Off for Purchase Receipt.
@frappe.whitelist()
def make_stock_entry(materialIssueList,mterialReceiptList,company):
	print "company-------------", company 
	materialItemsIssue=eval(materialIssueList)
	mterialItemsReceipt=eval(mterialReceiptList)
	basic_rate = 0
	ret = ""
	difference_account = frappe.db.get_single_value("Stock Settings", "material_round_off_amounts_changed_to")
	print "difference_account -------------", difference_account 
	if(len(materialItemsIssue)!=0):
		outerJson_Transfer = {
			"naming_series": "STE-",
			"doctype": "Stock Entry",
			"title": "Material Issue",
			"docstatus": 1,
			"purpose": "Material Issue",
			"company": company,
			"items": []
					}
		for items in materialItemsIssue:
			if items['rate'] is not None:
				basic_rate = items['rate']

			innerJson_Transfer =	{
				"s_warehouse":items['warehouse'],
				"qty":items['qty'],
				"item_code":items['item_code'],
				"basic_rate": basic_rate,
				"doctype": "Stock Entry Detail"
			}
			if difference_account is not None:
				innerJson_Transfer["expense_account"] = difference_account
			outerJson_Transfer["items"].append(innerJson_Transfer)
		print "########-Final make_stock_entry Json::", outerJson_Transfer
		doc = frappe.new_doc("Stock Entry")
		doc.update(outerJson_Transfer)
		doc.save()
		ret = doc.doctype
		if ret:
			frappe.msgprint("Stock entry is created for Material Issue : "+doc.name)

	if(len(mterialItemsReceipt)!=0):
		outerJson_Transfer = {
			"naming_series": "STE-",
			"doctype": "Stock Entry",
			"title": "Material Receipt",
			"docstatus": 1,
			"purpose": "Material Receipt",
			"company": company,
			"items": []
			}
		for items in mterialItemsReceipt:
			if items['rate'] is not None:
				basic_rate = items['rate']
			innerJson_Transfer =	{
				"t_warehouse":items['warehouse'],
				"qty":items['qty'],
				"item_code":items['item_code'],
				"basic_rate": basic_rate,
				"doctype": "Stock Entry Detail"
			}
			if difference_account is not None:
				innerJson_Transfer["expense_account"] = difference_account
			outerJson_Transfer["items"].append(innerJson_Transfer)
		print "########-Final make_stock_entry Json::", outerJson_Transfer
		doc = frappe.new_doc("Stock Entry")
		doc.update(outerJson_Transfer)
		doc.save()
		ret = doc.doctype
		if ret:
			frappe.msgprint("Stock entry is created for Material Receipt : "+doc.name)
## End of- Rounding and Charging Off for Purchase Receipt.

@frappe.whitelist()
def fetch_delivery_note_list(name):
	delivery_note_list = frappe.db.sql("""select name from `tabDelivery Note` where pch_sales_invoice=%s """, name, as_dict = 1) 
	return delivery_note_list

## Expense Account details of Stock Entry Begins...
@frappe.whitelist()
def match_item_code(purpose):
	details = frappe.db.sql("""select purpose,expense_account from `tabStock Expense Account Details` where purpose = %s""",(purpose), as_dict=1)
	print "details------", details
	return details
## Expense Account details of Stock Entry end...

