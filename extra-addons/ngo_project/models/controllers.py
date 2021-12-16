# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import http
from openerp.http import request
from openerp.addons.web.controllers.main import serialize_exception,content_disposition
import base64

class Binary(http.Controller):
	@http.route('/web/binary/download_document',type='http',auth="public")
	@serialize_exception
	def download_document(self,model,field,id,filename=None, **kw):
		""" Download link for files stored as binary fields.
			:param str model: name of the model to fetch the binary from
			:param str field: binary field
			:param str id: id of the record from which to fetch the binary
			:param str filename: field holding the file's name, if any
			:returns: :class:`werkzeug.wrappers.Response`
		"""
		Model = request.registry[model]
		cr, uid, context = request.cr, request.uid, request.context
		fields = [field]
		res = Model.read(cr, uid, [int(id)],fields,context)[0]
		filecontent = base64.b64decode(res.get(field) or '')
		
		if not filecontent:
			return request.not_found()
		else:
			if not filename:
				filename = '%s_%s' % (model.replace('.','_'),id)
			return request.make_response(filecontent,[('Content-Type','application/octet-stream'),('Content-Disposition',content_disposition(filename))])

