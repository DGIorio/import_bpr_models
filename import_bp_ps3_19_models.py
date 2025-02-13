#-*- coding:utf-8 -*-

## TO DO

# material state: proper port
# texture state properties: all
# raster properties: unks

#

import bpy
from bpy_extras.io_utils import (
	axis_conversion
)
import bmesh
import binascii
import math
from mathutils import Matrix, Vector
import os
import time
import struct
from numpy import frombuffer
from bundle_packer_unpacker import unpack_bundle
import tempfile
import zlib


def main_ps3_bp_19(context, file_path, resource_type, is_bundle, clear_scene, debug_prefer_shared_asset):
	## INITIALIZING
	start_time = time.time()
	
	print("Importing file %s" % os.path.basename(file_path))
	print("Initializing variables...")
	if is_bundle == True:
		temp_dir = tempfile.TemporaryDirectory()
		directory_path = temp_dir.name
	else:
		directory_path = os.path.dirname(os.path.dirname(file_path))
	instancelist_dir = os.path.join(directory_path, "InstanceList")
	propinstancedata_dir = os.path.join(directory_path, "PropInstanceData")
	propgraphicslist_dir = os.path.join(directory_path, "PropGraphicsList")
	staticsoundmap_dir = os.path.join(directory_path, "StaticSoundMap")
	polygonsouplist_dir = os.path.join(directory_path, "PolygonSoupList")
	
	graphicsstub_dir = os.path.join(directory_path, "GraphicsStub")
	graphicsspec_dir = os.path.join(directory_path, "GraphicsSpec")
	wheelgraphicsspec_dir = os.path.join(directory_path, "WheelGraphicsSpec")
	model_dir = os.path.join(directory_path, "Model")
	renderable_dir = os.path.join(directory_path, "Renderable")
	vertex_descriptor_dir = os.path.join(directory_path, "VertexDesc")
	material_dir = os.path.join(directory_path, "Material")
	material_technique_dir = os.path.join(directory_path, "MaterialTechnique")
	material_technique_old_dir = os.path.join(directory_path, "0D (console only)")
	texturestate_dir = os.path.join(directory_path, "TextureState")
	raster_dir = os.path.join(directory_path, "Raster")
	
	deformationspec_dir = os.path.join(directory_path, "StreamedDeformationSpec")
	
	shared_dir = os.path.join(BurnoutLibraryGet(), "BP_Library_PS3")
	shared_model_dir = os.path.join(shared_dir, "Model")
	shared_renderable_dir = os.path.join(shared_dir, "Renderable")
	shared_vertex_descriptor_dir = os.path.join(shared_dir, "VertexDesc")
	shared_material_dir = os.path.join(shared_dir, "Material")
	shared_material_technique_dir = os.path.join(shared_dir, "MaterialTechnique")
	shared_shader_dir = os.path.join(os.path.join(shared_dir, "SHADERS"), "Shader")
	shared_texturestate_dir = os.path.join(shared_dir, "TextureState")
	shared_raster_dir = os.path.join(shared_dir, "Raster")
	
	instances = []
	models = {}
	renderables = []
	vertex_descriptors = []
	materials = []
	shaders = []
	texture_states = []
	rasters = []
	PolygonSoups = []
	
	m = axis_conversion(from_forward='-Y', from_up='Z', to_forward='-Z', to_up='X').to_4x4()
	
	## UNPACKING FILE
	if is_bundle == True:
		print("Unpacking file...")
		unpacking_time = time.time()
		
		status = unpack_bundle(file_path, directory_path, "IDs_" + os.path.basename(file_path))
		
		elapsed_time = time.time() - unpacking_time
		
		if status == 1:
			return {'CANCELLED'}
		print("... %.4fs" % elapsed_time)
		
		if resource_type == "InstanceList":
			if not os.path.isdir(instancelist_dir):
				print("ERROR: non-existent path %s. Verify if you selected the correct resource type to import and try again. You had selected to import the file as %s." % (instancelist_dir, resource_type))
				return {'CANCELLED'}
			file_path = os.path.join(instancelist_dir, os.listdir(instancelist_dir)[0])
		
		elif resource_type == "GraphicsStub":
			if not os.path.isdir(graphicsstub_dir):
				print("ERROR: non-existent path %s. Verify if you selected the correct resource type to import and try again. You had selected to import the file as %s." % (graphicsstub_dir, resource_type))
				return {'CANCELLED'}
			file_path = os.path.join(graphicsstub_dir, os.listdir(graphicsstub_dir)[0])
		
		elif resource_type == "GraphicsSpec":
			if not os.path.isdir(graphicsspec_dir):
				print("ERROR: non-existent path %s. Verify if you selected the correct resource type to import and try again. You had selected to import the file as %s." % (graphicsspec_dir, resource_type))
				return {'CANCELLED'}
			file_path = os.path.join(graphicsspec_dir, os.listdir(graphicsspec_dir)[0])
		
		elif resource_type == "WheelGraphicsSpec":
			if not os.path.isdir(wheelgraphicsspec_dir):
				print("ERROR: non-existent path %s. Verify if you selected the correct resource type to import and try again. You had selected to import the file as %s." % (wheelgraphicsspec_dir, resource_type))
				return {'CANCELLED'}
			file_path = os.path.join(wheelgraphicsspec_dir, os.listdir(wheelgraphicsspec_dir)[0])
		
		elif resource_type == "StreamedDeformationSpec":
			if not os.path.isdir(deformationspec_dir):
				print("ERROR: non-existent path %s. Verify if you selected the correct resource type to import and try again. You had selected to import the file as %s." % (deformationspec_dir, resource_type))
				return {'CANCELLED'}
			file_path = os.path.join(deformationspec_dir, os.listdir(deformationspec_dir)[0])
		
		elif resource_type == "PolygonSoupList":
			if not os.path.isdir(polygonsouplist_dir):
				print("ERROR: non-existent path %s. Verify if you selected the correct resource type to import and try again. You had selected to import the file as %s." % (polygonsouplist_dir, resource_type))
				return {'CANCELLED'}
			file_path = polygonsouplist_dir
	
	## PARSING FILES
	print("Parsing files...")
	parsing_time = time.time()
	
	mMainId = os.path.splitext(os.path.basename(file_path))[0]
	if resource_type == "InstanceList":
		track_unit_number = decode_resource_id(mMainId, resource_type)
		track_unit_number = int(track_unit_number.replace("TRK_UNIT", ""))
		
		mpaInstances, muArraySize, muNumInstances, muVersionNumber, instances = read_instancelist(file_path)
		
		mInstanceList = "TRK_UNIT" + str(track_unit_number) + "_list"
		mPropGraphicsList = "PRP_GL__" + str(track_unit_number)
		mPropInstanceData = "PRP_INST_" + str(track_unit_number)
		mStaticSoundMap_emitter = "TRK_UNIT" + str(track_unit_number) + "_Emitter"
		mStaticSoundMap_passby = "TRK_UNIT" + str(track_unit_number) + "_Passby"
		
		mPropGraphicsListId = calculate_resourceid(mPropGraphicsList.lower())
		mPropInstanceDataId = calculate_resourceid(mPropInstanceData.lower())
		mStaticSoundMapId_emitter = calculate_resourceid(mStaticSoundMap_emitter.lower())
		mStaticSoundMapId_passby = calculate_resourceid(mStaticSoundMap_passby.lower())
		
		propgraphicslist_path = os.path.join(propgraphicslist_dir, mPropGraphicsListId + ".dat")
		propinstancedata_path = os.path.join(propinstancedata_dir, mPropInstanceDataId + ".dat")
		staticsoundmap_emitter_path = os.path.join(staticsoundmap_dir, mStaticSoundMapId_emitter + ".dat")
		staticsoundmap_passby_path = os.path.join(staticsoundmap_dir, mStaticSoundMapId_passby + ".dat")
		
		prop_info, prop_part_info = read_propgraphicslist(propgraphicslist_path)
		instances_props, unk1s_props = read_propinstancedata(propinstancedata_path, prop_info, prop_part_info)
		
		emitter_data = read_staticsoundmap(staticsoundmap_emitter_path)
		passby_data = read_staticsoundmap(staticsoundmap_passby_path)
		
		instances += instances_props
		
	elif resource_type == "GraphicsStub":
		vehicle_name = decode_resource_id(mMainId, resource_type)
		mGraphicsSpec = vehicle_name + "_Graphics"
		
		mGraphicsSpec_info, mWheelGraphicsSpec_info = read_graphicsstub(file_path)
		mGraphicsSpecId = mGraphicsSpec_info[0]
		mWheelGraphicsSpecId = mWheelGraphicsSpec_info[0]
		
		wheel_name = decode_resource_id(mWheelGraphicsSpecId, "WheelGraphicsSpec")
		mWheelGraphicsSpec = wheel_name + "_Graphics"
		
		graphicsspec_path = os.path.join(graphicsspec_dir, mGraphicsSpecId + ".dat")
		wheelgraphicsspec_path = os.path.join(directory_path, "WheelGraphicsSpec", mWheelGraphicsSpecId + ".dat")
		
		muVersionNumber, instances = read_graphicsspec(graphicsspec_path)
		muVersionNumber_wheel, instances_wheel = read_wheelgraphicsspec(wheelgraphicsspec_path)
		instances += instances_wheel
		
	elif resource_type == "GraphicsSpec":
		vehicle_name = decode_resource_id(mMainId, resource_type)
		mGraphicsSpec = vehicle_name + "_Graphics"
		muVersionNumber, instances = read_graphicsspec(file_path)
		
	elif resource_type == "WheelGraphicsSpec":
		wheel_name = decode_resource_id(mMainId, resource_type)
		mWheelGraphicsSpec = wheel_name + "_Graphics"
		muVersionNumber, instances = read_wheelgraphicsspec(file_path)
	
	elif resource_type == "StreamedDeformationSpec":
		vehicle_name = decode_resource_id(mMainId, resource_type)
		mStreamedDeformationSpec = vehicle_name + "deformationmodel"
		mCarModelSpaceToHandlingBodySpaceTransform, HandlingBodyDimensions, WheelSpecs, SensorSpecs, SpecID, mNums, OffsetsAndTensor, TagPointSpecs, DrivenPoints, GenericTags, CameraTags, LightTags, IKParts, GlassPanes = read_deformationspec(file_path)
		
		NumVehicleBodies, NumGraphicsParts = mNums
		CurrentCOMOffset, MeshOffset, RigidBodyOffset, CollisionOffset, InertiaTensor = OffsetsAndTensor
	
	elif resource_type == "PolygonSoupList":
		world_collision = []
		if os.path.isfile(file_path):
			track_unit_number = decode_resource_id(mMainId, resource_type)
			track_unit_number = int(track_unit_number.replace("TRK_COL_", ""))
			mPolygonSoupList = "TRK_COL_" + str(track_unit_number)
			
			PolygonSoups = read_polygonsouplist(file_path)
			world_collision.append([track_unit_number, mPolygonSoupList, PolygonSoups])
		
		elif os.path.isdir(file_path):
			for file in os.listdir(file_path):
				file2_path = os.path.join(file_path, file)
				mMainId = os.path.splitext(os.path.basename(file2_path))[0]
				track_unit_number = decode_resource_id(mMainId, resource_type)
				track_unit_number = int(track_unit_number.replace("TRK_COL_", ""))
				mPolygonSoupList = "TRK_COL_" + str(track_unit_number)
				
				PolygonSoups = read_polygonsouplist(file2_path)
				world_collision.append([track_unit_number, mPolygonSoupList, PolygonSoups])
	
	models_not_found = []
	for i in range(0, len(instances)):
		mModelId = instances[i][0]
		
		if mModelId in models:
			continue
		
		is_shared_asset = False
		
		model_path = os.path.join(model_dir, mModelId + ".dat")
		if not os.path.isfile(model_path):
			model_path = os.path.join(shared_model_dir, mModelId + ".dat")
			is_shared_asset = True
			if not os.path.isfile(model_path):
				print("WARNING: failed to open model %s: no such file in '%s' and '%s'. Ignoring it." % (mModelId, model_dir, shared_model_dir))
				models_not_found.append(i)
				continue
		
		model_properties, renderables_info = read_model(model_path)
		models[mModelId] = [mModelId, [renderables_info, model_properties], is_shared_asset]
	
	for index in reversed(models_not_found):
		del instances[index]
	
	for model in models:
		for renderable_info in models[model][1][0]:
			mRenderableId = renderable_info[0]
			if mRenderableId in (rows[0] for rows in renderables):
				continue
			
			is_shared_asset = False
			
			renderable_path = os.path.join(renderable_dir, mRenderableId + ".dat")
			if not os.path.isfile(renderable_path):
				renderable_path = os.path.join(shared_renderable_dir, mRenderableId + ".dat")
				is_shared_asset = True
				if not os.path.isfile(renderable_path):
					print("WARNING: failed to open renderable %s: no such file in '%s' and '%s'." % (mRenderableId, renderable_dir, shared_renderable_dir))
					continue
			
			renderable_properties, meshes_info = read_renderable(renderable_path)
			renderables.append([mRenderableId, [meshes_info, renderable_properties], is_shared_asset, renderable_path])
	
	for i in range(0, len(renderables)):
		for mesh_info in renderables[i][1][0]:
			mVertexDescriptorId_main = mesh_info[-1][0]
			if mVertexDescriptorId_main in (rows[0] for rows in vertex_descriptors):
				continue
			
			vertex_descriptor_path = os.path.join(vertex_descriptor_dir, mVertexDescriptorId_main + ".dat")
			if not os.path.isfile(vertex_descriptor_path):
				vertex_descriptor_path = os.path.join(shared_vertex_descriptor_dir, mVertexDescriptorId_main + ".dat")
				is_shared_asset = True
				if not os.path.isfile(vertex_descriptor_path):
					print("WARNING: failed to open vertex descriptor %s: no such file in '%s' and '%s'." % (mVertexDescriptorId_main, vertex_descriptor_dir, shared_vertex_descriptor_dir))
					continue
			
			vertex_properties = read_vertex_descriptor(vertex_descriptor_path)
			vertex_descriptors.append([mVertexDescriptorId_main, [vertex_properties], is_shared_asset])
	
	for i in range(0, len(renderables)):
		for mesh_info in renderables[i][1][0]:
			mMaterialId = mesh_info[2]
			if mMaterialId in (rows[0] for rows in materials):
				continue
			
			is_shared_asset = False
			
			material_path = os.path.join(material_dir, mMaterialId + ".dat")
			if not os.path.isfile(material_path):
				material_path = os.path.join(shared_material_dir, mMaterialId + ".dat")
				is_shared_asset = True
				if not os.path.isfile(material_path):
					print("WARNING: failed to open material %s: no such file in '%s' and '%s'." % (mMaterialId, material_dir, shared_material_dir))
					continue
			
			material_properties, mShaderId, material_states_info, texture_states_info = read_material(material_path, material_technique_dir, shared_material_technique_dir, material_technique_old_dir)
			materials.append([mMaterialId, [mShaderId, material_states_info, texture_states_info, material_properties], is_shared_asset])
	
	for i in range(0, len(materials)):
		mShaderId = materials[i][1][0]
		if mShaderId in (rows[0] for rows in shaders):
			continue
			
		shader_path = os.path.join(shared_shader_dir, mShaderId + ".dat")
		is_shared_asset = True
		if not os.path.isfile(shader_path):
			print("WARNING: failed to open shader %s: no such file in '%s'." % (mShaderId, shared_shader_dir))
			continue
			
		shader_type, raster_types, muNumVertexShaderConstantsInstances, muNumPixelShaderConstantsInstances = read_shader(shader_path)
		shaders.append([mShaderId, [raster_types], shader_type, muNumVertexShaderConstantsInstances, muNumPixelShaderConstantsInstances, is_shared_asset])
	
	for i in range(0, len(materials)):
		for texture_state_info in materials[i][1][2]:
			mTextureStateId = texture_state_info[0]
			if mTextureStateId in (rows[0] for rows in texture_states):
				continue
			
			is_shared_asset = False
			
			texture_state_path = os.path.join(texturestate_dir, mTextureStateId + ".dat")
			if not os.path.isfile(texture_state_path):
				texture_state_path = os.path.join(shared_texturestate_dir, mTextureStateId + ".dat")
				is_shared_asset = True
				if not os.path.isfile(texture_state_path):
					print("WARNING: failed to open textureState %s: no such file in '%s' and '%s'." % (mTextureStateId, texturestate_dir, shared_texturestate_dir))
					continue
			
			texture_state_properties, raster_info = read_textureState(texture_state_path)
			texture_states.append([mTextureStateId, [raster_info, texture_state_properties], is_shared_asset])

	for i in range(0, len(texture_states)):
		for raster_info in texture_states[i][1][0]:
			mRasterId = raster_info[0]
			if mRasterId in (rows[0] for rows in rasters):
				continue
			
			is_shared_asset = False
			
			raster_path = os.path.join(raster_dir, mRasterId + ".dat")
			if not os.path.isfile(raster_path):
				raster_path = os.path.join(shared_raster_dir, mRasterId + ".dat")
				is_shared_asset = True
				if not os.path.isfile(raster_path):
					raster_path = os.path.join(shared_raster_dir, mRasterId + ".dds")
					if not os.path.isfile(raster_path):
						print("WARNING: failed to open raster %s: no such file in '%s' and '%s'." % (mRasterId, raster_dir, shared_raster_dir))
						continue
			
			if debug_prefer_shared_asset == True:
				raster_path_shared = os.path.join(shared_raster_dir, mRasterId + ".dat")
				raster_path_shared_dds = os.path.join(shared_raster_dir, mRasterId + ".dds")
				if os.path.isfile(raster_path_shared):
					raster_path = raster_path_shared
					is_shared_asset = True
				elif os.path.isfile(raster_path_shared_dds):
					raster_path = raster_path_shared_dds
					is_shared_asset = True
			
			raster_properties = read_raster(raster_path)
			rasters.append([mRasterId, [raster_properties], is_shared_asset, raster_path])
	
	elapsed_time = time.time() - parsing_time
	print("... %.4fs" % elapsed_time)
	
	## IMPORTING TO SCENE
	print("Importing data to scene...")
	importing_time = time.time()
	
	# Main file
	main_collection_name = decode_resource_id(mMainId, resource_type)
	if resource_type in ("GraphicsStub", "GraphicsSpec"):
		main_collection_name += "_GR"
	elif resource_type == "StreamedDeformationSpec":
		main_collection_name += "_AT"
	elif resource_type == "PolygonSoupList":
		main_collection_name = "WORLDCOL"
	
	if resource_type == "PolygonSoupList":
		main_collection = bpy.data.collections.get(main_collection_name)
		if main_collection == None:
			main_collection = bpy.data.collections.new(main_collection_name)
			bpy.context.scene.collection.children.link(main_collection)
			main_collection["resource_type"] = resource_type
	else:
		main_collection = bpy.data.collections.new(main_collection_name)
		bpy.context.scene.collection.children.link(main_collection)
		main_collection["resource_type"] = resource_type
	
	if resource_type == "InstanceList":
		instancelist_collection = bpy.data.collections.new(mInstanceList)
		prop_collection = bpy.data.collections.new(mPropInstanceData)
		staticsoundmap_emitter_collection = bpy.data.collections.new(mStaticSoundMap_emitter)
		staticsoundmap_passby_collection = bpy.data.collections.new(mStaticSoundMap_passby)
		
		instancelist_collection["resource_type"] = "InstanceList"
		prop_collection["resource_type"] = "PropInstanceData"
		staticsoundmap_emitter_collection["resource_type"] = "StaticSoundMap_emitter"
		staticsoundmap_passby_collection["resource_type"] = "StaticSoundMap_passby"
		
		prop_collection["num_unk1s"] = len(unk1s_props)
		for i, unk1_prop in enumerate(unk1s_props):
			prop_collection["unk1_%d" % i] = unk1_prop
		
		main_collection.children.link(instancelist_collection)
		main_collection.children.link(prop_collection)
		main_collection.children.link(staticsoundmap_emitter_collection)
		main_collection.children.link(staticsoundmap_passby_collection)
	elif resource_type == "GraphicsStub":
		graphicsspec_collection = bpy.data.collections.new(mGraphicsSpec)
		wheelgraphicsspec_collection = bpy.data.collections.new(mWheelGraphicsSpec)
		graphicsspec_collection["resource_type"] = "GraphicsSpec"
		wheelgraphicsspec_collection["resource_type"] = "WheelGraphicsSpec"
		
		mpVehicleGraphics_index = mGraphicsSpec_info[1]
		mpWheelGraphics_index = mWheelGraphicsSpec_info[1]
		main_collection["VehicleGraphics_index"] = mpVehicleGraphics_index
		main_collection["WheelGraphics_index"] = mpWheelGraphics_index
		
		main_collection.children.link(graphicsspec_collection)
		main_collection.children.link(wheelgraphicsspec_collection)
	elif resource_type == "GraphicsSpec":
		graphicsspec_collection = bpy.data.collections.new(mGraphicsSpec)
		graphicsspec_collection["resource_type"] = "GraphicsSpec"
		main_collection.children.link(graphicsspec_collection)
	elif resource_type == "WheelGraphicsSpec":
		wheelgraphicsspec_collection = bpy.data.collections.new(mWheelGraphicsSpec)
		wheelgraphicsspec_collection["resource_type"] = "WheelGraphicsSpec"
		main_collection.children.link(wheelgraphicsspec_collection)
	elif resource_type == "StreamedDeformationSpec":
		deformationspec_collection = bpy.data.collections.new(mStreamedDeformationSpec)
		wheelsspec_collection = bpy.data.collections.new("WheelSpecs_" + vehicle_name)
		sensorspecs_collection = bpy.data.collections.new("SensorSpecs_" + vehicle_name)
		tagpointspecs_collection = bpy.data.collections.new("TagPointSpecs_" + vehicle_name)
		drivenpoints_collection = bpy.data.collections.new("DrivenPoints_" + vehicle_name)
		generictags_collection = bpy.data.collections.new("GenericTags_" + vehicle_name)
		cameratags_collection = bpy.data.collections.new("CameraTags_" + vehicle_name)
		lighttags_collection = bpy.data.collections.new("LightTags_" + vehicle_name)
		ikparts_collection = bpy.data.collections.new("IKParts_" + vehicle_name)
		glasspanes_collection = bpy.data.collections.new("GlassPanes_" + vehicle_name)
		
		deformationspec_collection["resource_type"] = "StreamedDeformationSpec"
		
		deformationspec_collection["position"] = mCarModelSpaceToHandlingBodySpaceTransform.translation[:]
		deformationspec_collection["quaternion"] = mCarModelSpaceToHandlingBodySpaceTransform.to_quaternion()[:]
		deformationspec_collection["scale"] = mCarModelSpaceToHandlingBodySpaceTransform.to_scale()[:]
		
		deformationspec_collection["HandlingBodyDimensions"] = HandlingBodyDimensions
		deformationspec_collection["SpecID"] = SpecID
		deformationspec_collection["NumVehicleBodies"] = NumVehicleBodies
		deformationspec_collection["NumGraphicsParts"] = NumGraphicsParts
		deformationspec_collection["CurrentCOMOffset"] = CurrentCOMOffset
		deformationspec_collection["MeshOffset"] = MeshOffset
		deformationspec_collection["RigidBodyOffset"] = RigidBodyOffset
		deformationspec_collection["CollisionOffset"] = CollisionOffset
		deformationspec_collection["InertiaTensor"] = InertiaTensor
		
		wheelsspec_collection["resource_type"] = "WheelSpecs"
		sensorspecs_collection["resource_type"] = "SensorSpecs"
		tagpointspecs_collection["resource_type"] = "TagPointSpecs"
		drivenpoints_collection["resource_type"] = "DrivenPoints"
		generictags_collection["resource_type"] = "GenericTags"
		cameratags_collection["resource_type"] = "CameraTags"
		lighttags_collection["resource_type"] = "LightTags"
		ikparts_collection["resource_type"] = "IKPart"
		glasspanes_collection["resource_type"] = "GlassPanes"
		
		main_collection.children.link(deformationspec_collection)
		deformationspec_collection.children.link(wheelsspec_collection)
		deformationspec_collection.children.link(sensorspecs_collection)
		deformationspec_collection.children.link(tagpointspecs_collection)
		deformationspec_collection.children.link(drivenpoints_collection)
		deformationspec_collection.children.link(generictags_collection)
		deformationspec_collection.children.link(cameratags_collection)
		deformationspec_collection.children.link(lighttags_collection)
		deformationspec_collection.children.link(ikparts_collection)
		deformationspec_collection.children.link(glasspanes_collection)
	elif resource_type == "PolygonSoupList":
		for collision in world_collision:
			track_unit_number, mPolygonSoupList, PolygonSoups = collision
			polygonsouplist_collection = bpy.data.collections.new(collision[1])
			polygonsouplist_collection["resource_type"] = "PolygonSoupList"
			main_collection.children.link(polygonsouplist_collection)
			collision.append(polygonsouplist_collection)
	
	for raster in rasters:
		raster_path = raster[-1]
		raster_properties = raster[1][0]
		is_shared_asset = raster[2]
		ext = os.path.splitext(raster_path)[1]
		
		raster_path = create_raster(raster_path, raster_properties)
		raster_image = bpy.data.images.load(raster_path, check_existing = True)
		raster_image.name = raster[0]
		
		raster_image["is_shared_asset"] = is_shared_asset
		if ext == ".dds":
			continue
		format, width, height, depth, dimension, mipmap = raster_properties
		raster_image["dimension"] = dimension
		
		if is_bundle == True:
			raster_image.pack()
	
	for material in materials:
		if bpy.data.materials.get(material[0]) is None:
			mMaterialId = material[0]
			mShaderId = material[1][0]
			material_states_info = material[1][1]
			texture_states_info = material[1][2]
			material_properties = material[1][3]
			unk_0x4_relative = material_properties[0][0]
			mafVertexShaderConstantsInstanceData, mauVertexShaderNamesHash = material_properties[0][1]
			mafPixelShaderConstantsInstanceData, mauPixelShaderNamesHash = material_properties[0][2]
			parameters_3, anim_strings_3 = material_properties[0][3]
			is_shared_asset = material[2]
			raster_types = {}
			shader_type = ""
			
			for shader in shaders:
				if shader[0] == mShaderId:
					raster_types = shader[1][0]
					shader_type = shader[2]
					break
			
			if shader[3] != len(mafVertexShaderConstantsInstanceData):
				print("WARNING: muNumVertexShaderConstantsInstances is different between material %s and shader %s." %(mMaterialId, mShaderId))
			
			if shader[4] != len(mafPixelShaderConstantsInstanceData):
				print("WARNING: muNumPixelShaderConstantsInstances is different between material %s and shader %s." %(mMaterialId, mShaderId))
			
			mat = bpy.data.materials.new(mMaterialId)
			mat.use_nodes = True
			mat.name = mMaterialId
			mat.node_tree.nodes["Principled BSDF"].name = mMaterialId
			
			if len(texture_states_info) > 0:
				for i in range(0, len(texture_states_info)):
					mTextureStateId = texture_states_info[i][0]
					texture_sampler_code = texture_states_info[i][1]
					try:
						raster_type = raster_types[texture_sampler_code]
					except:
						print("WARNING: raster type (channel) not defined by shader %s, found in material %s. It is defined as %d" % (mShaderId, mMaterialId, texture_sampler_code))
						raster_type = "Undefined"
					for texture_state in texture_states:
						if texture_state[0] == mTextureStateId:
							mRasterId = texture_state[1][0][0][0]
							addressing_mode, filter_types, min_max_lod, max_anisotropy, mipmap_lod_bias, comparison_function, is_border_color_white, unk1 = texture_state[1][1]
							is_shared_asset = texture_state[-1]
							break
					else:
						continue
					
					mat_tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
					mat_tex.image = bpy.data.images.get(mRasterId)
					mat_tex.name = raster_type
					mat_tex.label = mTextureStateId
					#mat_tex["addressing_mode"] = addressing_mode
					#mat_tex["filter_types"] = filter_types
					#mat_tex["min_max_lod"] = min_max_lod
					#mat_tex["max_anisotropy"] = max_anisotropy
					#mat_tex["mipmap_lod_bias"] = mipmap_lod_bias
					#mat_tex["comparison_function"] = comparison_function
					#mat_tex["is_border_color_white"] = is_border_color_white
					#mat_tex["unk1"] = unk1
					mat_tex["is_shared_asset"] = is_shared_asset
					if raster_type == "DiffuseTextureSampler":
						mat.node_tree.links.new(mat.node_tree.nodes[mMaterialId].inputs[0], mat_tex.outputs[0])
			
				if shader_type == "Vehicle_Opaque_PaintGloss_Textured_Damaged" or shader_type == "Vehicle_Opaque_PaintGloss_Textured_Traffic_Damaged":
					mix_rgb_node = mat.node_tree.nodes.new(type='ShaderNodeMixRGB')
					
					mat.node_tree.links.new(mix_rgb_node.inputs[0], mat.node_tree.nodes['DiffuseTextureSampler'].outputs[1])
					mat.node_tree.links.new(mix_rgb_node.inputs[2], mat.node_tree.nodes['DiffuseTextureSampler'].outputs[0])
					mat.node_tree.links.new(mix_rgb_node.outputs[0], mat.node_tree.nodes[mMaterialId].inputs[0])
					mat.node_tree.nodes[mMaterialId].inputs[9].default_value = 0.25
					mat.node_tree.nodes[mMaterialId].inputs[6].default_value = 0.3
				
				elif shader_type == "Vehicle_GreyScale_Decal_Textured_Damaged":
					mat_tex = mat.node_tree.nodes['DiffuseTextureSampler']
					mat.node_tree.links.new(mat_tex.outputs[1], mat.node_tree.nodes[mMaterialId].inputs[21])
					mat.node_tree.nodes[mMaterialId].inputs[6].default_value = 0.3
					mat.blend_method = 'HASHED'
					mat.shadow_method = 'HASHED'
				
				elif shader_type == "Vehicle_Livery_Alpha_CarGuts_Damaged":
					mat_tex = mat.node_tree.nodes['DiffuseTextureSampler']
					mat.node_tree.links.new(mat_tex.outputs[1], mat.node_tree.nodes[mMaterialId].inputs[21])
					mat.node_tree.nodes[mMaterialId].inputs[6].default_value = 0.3
					mat.blend_method = 'HASHED'
					mat.shadow_method = 'HASHED'
				
				elif shader_type == "Vehicle_Opaque_PlasticMatt_Damaged":
					mat.node_tree.nodes[mMaterialId].inputs[0].default_value = (0.005, 0.005, 0.005, 1.0)
					mat.node_tree.nodes[mMaterialId].inputs[9].default_value = 0.3
					mat.node_tree.nodes[mMaterialId].inputs[6].default_value = 0.1
					mat.node_tree.nodes[mMaterialId].inputs[7].default_value = 0.4
				
				elif shader_type == "Vehicle_Opaque_Chrome_Damaged_Damaged":
					mat.node_tree.nodes[mMaterialId].inputs[9].default_value = 0.05
					mat.node_tree.nodes[mMaterialId].inputs[6].default_value = 1.0
					mat.node_tree.nodes[mMaterialId].inputs[7].default_value = 0.0
				
				elif shader_type == "Vehicle_Greyscale_Window_Textured_Damaged":
					mix_rgb_node = mat.node_tree.nodes.new(type='ShaderNodeMixRGB')
					
					mat.node_tree.links.new(mat.node_tree.nodes['DiffuseTextureSampler'].outputs[0], mix_rgb_node.inputs[2])
					mix_rgb_node.inputs[1].default_value = mafPixelShaderConstantsInstanceData[3]
					mat.node_tree.links.new(mix_rgb_node.outputs[0], mat.node_tree.nodes[mMaterialId].inputs[0])
					
					mat.node_tree.nodes[mMaterialId].inputs[9].default_value = 0.0
					mat.node_tree.nodes[mMaterialId].inputs[17].default_value = 1.0
					
					mat.use_screen_refraction = True
					mat.refraction_depth = 0.01
					
					bpy.context.scene.eevee.use_ssr = True
					bpy.context.scene.eevee.use_ssr_refraction = True
				
				elif shader_type == "Vehicle_1Bit_MetalFaded_Textured_EnvMapped_Damaged":
					mat.node_tree.nodes[mMaterialId].inputs[6].default_value = 0.5
				
				elif shader_type == "Vehicle_1Bit_Tyre_Textured" or shader_type == "Vehicle_1Bit_Tyre_Textured_Blurred":
					mat.node_tree.nodes[mMaterialId].inputs[7].default_value = 0.0
					mat.node_tree.nodes[mMaterialId].inputs[9].default_value = 1.0
				
				elif shader_type == "Vehicle_GreyScale_WheelChrome_Textured_Damaged" or shader_type == "Vehicle_GreyScale_WheelChrome_Textured_Damaged_Blurred":
					mat.node_tree.nodes[mMaterialId].inputs[6].default_value = 1.0
					mat.node_tree.nodes[mMaterialId].inputs[9].default_value = 0.2
					mat_tex = mat.node_tree.nodes['DiffuseTextureSampler']
					mat.node_tree.links.new(mat_tex.outputs[1], mat.node_tree.nodes[mMaterialId].inputs[21])
					mat.blend_method = 'HASHED'
					mat.shadow_method = 'HASHED'
				
				#World
				elif shader_type == "Road_Detailmap_Opaque_Singlesided_Default" or shader_type == "Road_Night_Detailmap_Opaque_Singlesided_Default" or shader_type == "Tunnel_Road_Detailmap_Opaque_Singlesided_Default" or shader_type == "Tunnel_Lightmapped_Road_Detailmap_Opaque_Singlesided2_Default":
					lineMapSampler_tex = mat.node_tree.nodes['lineMapSampler']
					detailMapSampler_tex = mat.node_tree.nodes['detailMapSampler']
					baseMapSampler_tex = mat.node_tree.nodes['baseMapSampler']
					
					mix_rgb_node1 = mat.node_tree.nodes.new(type='ShaderNodeMixRGB')
					mix_rgb_node2 = mat.node_tree.nodes.new(type='ShaderNodeMixRGB')
					uv_map_node = mat.node_tree.nodes.new(type='ShaderNodeUVMap')
					vector_math_node = mat.node_tree.nodes.new(type='ShaderNodeVectorMath')
					
					uv_map_node.uv_map = "UVMap"
					vector_math_node.operation = "MULTIPLY"
					vector_math_node.inputs[1].default_value = mafPixelShaderConstantsInstanceData[1][:3]
					mat.node_tree.links.new(uv_map_node.outputs[0], vector_math_node.inputs[0])
					mat.node_tree.links.new(vector_math_node.outputs[0], detailMapSampler_tex.inputs[0])
					mat.node_tree.links.new(lineMapSampler_tex.outputs[0], mix_rgb_node1.inputs[1])
					mat.node_tree.links.new(detailMapSampler_tex.outputs[0], mix_rgb_node1.inputs[2])
					
					mix_rgb_node2.blend_type = "OVERLAY"
					mat.node_tree.links.new(mix_rgb_node1.outputs[0], mix_rgb_node2.inputs[1])
					mat.node_tree.links.new(baseMapSampler_tex.outputs[0], mix_rgb_node2.inputs[2])
					
					mat.node_tree.links.new(mix_rgb_node2.outputs[0], mat.node_tree.nodes[mMaterialId].inputs[0])
				
				elif shader_type == "DriveableSurface_Detailmap_Opaque_Singlesided_Default" or shader_type == "DriveableSurface_Night_Detailmap_Opaque_Singlesided_Default" or shader_type == "Tunnel_DriveableSurface_Detailmap_Opaque_Singlesided_Default":
					detailMapSampler_tex = mat.node_tree.nodes['detailMapSampler']
					baseMapSampler_tex = mat.node_tree.nodes['baseMapSampler']
					
					mix_rgb_node1 = mat.node_tree.nodes.new(type='ShaderNodeMixRGB')
					uv_map_node = mat.node_tree.nodes.new(type='ShaderNodeUVMap')
					vector_math_node = mat.node_tree.nodes.new(type='ShaderNodeVectorMath')
					
					uv_map_node.uv_map = "UVMap"
					vector_math_node.operation = "MULTIPLY"
					vector_math_node.inputs[1].default_value = mafPixelShaderConstantsInstanceData[1][:3]
					mat.node_tree.links.new(uv_map_node.outputs[0], vector_math_node.inputs[0])
					mat.node_tree.links.new(vector_math_node.outputs[0], detailMapSampler_tex.inputs[0])
					mix_rgb_node1.blend_type = "OVERLAY"
					mat.node_tree.links.new(baseMapSampler_tex.outputs[0], mix_rgb_node1.inputs[1])
					mat.node_tree.links.new(detailMapSampler_tex.outputs[0], mix_rgb_node1.inputs[2])
					
					mat.node_tree.links.new(mix_rgb_node1.outputs[0], mat.node_tree.nodes[mMaterialId].inputs[0])
					mat.node_tree.nodes[mMaterialId].inputs[7].default_value = 0.0
				
				elif shader_type == "DriveableSurface_DetailMap_Diffuse_Opaque_Singlesided_Default":
					detailMapSampler_tex = mat.node_tree.nodes['detailMapSampler']
					baseMapSampler_tex = mat.node_tree.nodes['baseMapSampler']
					
					mix_rgb_node1 = mat.node_tree.nodes.new(type='ShaderNodeMixRGB')
					uv_map_node = mat.node_tree.nodes.new(type='ShaderNodeUVMap')
					vector_math_node = mat.node_tree.nodes.new(type='ShaderNodeVectorMath')
					
					uv_map_node.uv_map = "UVMap"
					vector_math_node.operation = "MULTIPLY"
					vector_math_node.inputs[1].default_value = mafPixelShaderConstantsInstanceData[0][:3]
					mat.node_tree.links.new(uv_map_node.outputs[0], vector_math_node.inputs[0])
					mat.node_tree.links.new(vector_math_node.outputs[0], detailMapSampler_tex.inputs[0])
					mix_rgb_node1.blend_type = "OVERLAY"
					mat.node_tree.links.new(baseMapSampler_tex.outputs[0], mix_rgb_node1.inputs[1])
					mat.node_tree.links.new(detailMapSampler_tex.outputs[0], mix_rgb_node1.inputs[2])
					
					mat.node_tree.links.new(mix_rgb_node1.outputs[0], mat.node_tree.nodes[mMaterialId].inputs[0])
					mat.node_tree.nodes[mMaterialId].inputs[7].default_value = 0.0
				
				elif shader_type == "Terrain_Diffuse_Opaque_Singlesided_Default":
					HorizontalFaceTextureSampler_tex = mat.node_tree.nodes['HorizontalFaceTextureSampler']
					VerticalFaceTextureSampler_tex = mat.node_tree.nodes['VerticalFaceTextureSampler']
					SlantedFaceTextureSampler_tex = mat.node_tree.nodes['SlantedFaceTextureSampler']
					
					mix_rgb_node1 = mat.node_tree.nodes.new(type='ShaderNodeMixRGB')
					mix_rgb_node2 = mat.node_tree.nodes.new(type='ShaderNodeMixRGB')
					uv_map_node = mat.node_tree.nodes.new(type='ShaderNodeUVMap')
					vector_math_node = mat.node_tree.nodes.new(type='ShaderNodeVectorMath')
					
					uv_map_node.uv_map = "UVMap"
					vector_math_node.operation = "MULTIPLY"
					vector_math_node.inputs[1].default_value = mafPixelShaderConstantsInstanceData[5][:3]
					mix_rgb_node1.inputs[0].default_value = 0.2
					mix_rgb_node2.inputs[0].default_value = 0.8
					
					mat.node_tree.links.new(uv_map_node.outputs[0], vector_math_node.inputs[0])
					mat.node_tree.links.new(vector_math_node.outputs[0], HorizontalFaceTextureSampler_tex.inputs[0])
					mat.node_tree.links.new(vector_math_node.outputs[0], SlantedFaceTextureSampler_tex.inputs[0])
					mat.node_tree.links.new(HorizontalFaceTextureSampler_tex.outputs[0], mix_rgb_node1.inputs[1])
					mat.node_tree.links.new(VerticalFaceTextureSampler_tex.outputs[0], mix_rgb_node1.inputs[2])
					
					mat.node_tree.links.new(mix_rgb_node1.outputs[0], mix_rgb_node2.inputs[1])
					mat.node_tree.links.new(SlantedFaceTextureSampler_tex.outputs[0], mix_rgb_node2.inputs[2])
					
					mat.node_tree.links.new(mix_rgb_node2.outputs[0], mat.node_tree.nodes[mMaterialId].inputs[0])
					mat.node_tree.nodes[mMaterialId].inputs[7].default_value = 0.0
				
				elif shader_type == "Water_Specular_Opaque_Singlesided_Default":
					tex_coord_node = mat.node_tree.nodes.new(type='ShaderNodeTexCoord')
					mapping_node = mat.node_tree.nodes.new(type='ShaderNodeMapping')
					musgrave_node = mat.node_tree.nodes.new(type='ShaderNodeTexMusgrave')
					bump_node = mat.node_tree.nodes.new(type='ShaderNodeBump')
					
					musgrave_node.inputs[2].default_value = 1500.0
					musgrave_node.inputs[3].default_value = 2.0
					musgrave_node.inputs[4].default_value = 1.2
					musgrave_node.inputs[5].default_value = 1.1
					bump_node.inputs[0].default_value = 0.1
					mat.node_tree.nodes[mMaterialId].inputs[0].default_value = mafPixelShaderConstantsInstanceData[0]
					mat.node_tree.nodes[mMaterialId].inputs[6].default_value = 0.9
					mat.node_tree.nodes[mMaterialId].inputs[9].default_value = 0.15
					
					mat.node_tree.links.new(tex_coord_node.outputs[0], mapping_node.inputs[0])
					mat.node_tree.links.new(mapping_node.outputs[0], musgrave_node.inputs[0])
					mat.node_tree.links.new(musgrave_node.outputs[0], bump_node.inputs[2])
					mat.node_tree.links.new(bump_node.outputs[0], mat.node_tree.nodes[mMaterialId].inputs[22])
				
				elif shader_type == "Foliage_1Bit_Doublesided_Default" or shader_type == "Diffuse_1Bit_Doublesided_Default" or shader_type == "Specular_1Bit_Singlesided_Default" or shader_type == "Specular_1Bit_Doublesided_Default" or shader_type == "Cruciform_1Bit_Doublesided_Default" or "1Bit" in shader_type:
					mat_tex = mat.node_tree.nodes['DiffuseTextureSampler']
					mat.node_tree.links.new(mat_tex.outputs[1], mat.node_tree.nodes[mMaterialId].inputs[21])
					mat.node_tree.nodes[mMaterialId].inputs[7].default_value = 0.0
					mat.blend_method = 'HASHED'
					mat.shadow_method = 'HASHED'
				
				elif shader_type == "Specular_Greyscale_Singlesided_Default" or shader_type == "Specular_Greyscale_Doublesided_Default":
					mat_tex = mat.node_tree.nodes['DiffuseTextureSampler']
					mat.node_tree.links.new(mat_tex.outputs[1], mat.node_tree.nodes[mMaterialId].inputs[21])
					mat.node_tree.nodes[mMaterialId].inputs[7].default_value = 0.0
					mat.blend_method = 'HASHED'
					mat.shadow_method = 'HASHED'
			
			# Properties
			mat["shader_type"] = shader_type
			mat["MaterialStateIds"] = [mMaterialStateId[0] for mMaterialStateId in material_states_info]
			if len(mafVertexShaderConstantsInstanceData) > 0:
				for i, parameter in enumerate(mafVertexShaderConstantsInstanceData):
					mat["VertexShaderConstantsInstanceData_entry_%d" % i] = parameter
				mat["VertexShaderNamesHash"] = mauVertexShaderNamesHash
			if len(mafPixelShaderConstantsInstanceData) > 0:
				for i, parameter in enumerate(mafPixelShaderConstantsInstanceData):
					mat["PixelShaderConstantsInstanceData_entry_%d" % i] = parameter
				mat["PixelShaderNamesHash"] = mauPixelShaderNamesHash
			if len(parameters_3) > 0:
				for i, parameter in enumerate(parameters_3):
					mat["parameters_3_entry_%d" % i] = parameter
				mat["anim_strings_3"] = anim_strings_3
			
			mat["is_shared_asset"] = is_shared_asset
	
	renderable_already_scene = []
	for renderable in renderables:
		mRenderableId = renderable[0]
		if mRenderableId in bpy.context.scene.objects:
			renderable_already_scene.append(mRenderableId)
			continue
		renderable_object = create_renderable(renderable, vertex_descriptors)
		main_collection.objects.link(renderable_object)
		
		renderable_properties = renderable[1][1]
		object_center = renderable_properties[0]
		object_radius = renderable_properties[1]
		mu16VersionNumber = renderable_properties[2]
		flags = renderable_properties[4]
		
		renderable_object["object_center"] = object_center
		renderable_object["object_radius"] = object_radius
		renderable_object["flags"] = flags
		renderable_object["is_shared_asset"] = renderable[2]
	
	# Models
	for i in range(0, len(instances)):
		mModelId = instances[i][0]
		model_empty = bpy.data.objects.new(mModelId, None)
		if resource_type == "InstanceList":
			if i < (len(instances) - len(instances_props)):
				instancelist_collection.objects.link(model_empty)
			else:
				prop_collection.objects.link(model_empty)
		elif resource_type == "GraphicsStub":
			if i < (len(instances) - len(instances_wheel)):
				graphicsspec_collection.objects.link(model_empty)
			else:
				wheelgraphicsspec_collection.objects.link(model_empty)
		elif resource_type == "GraphicsSpec":
			graphicsspec_collection.objects.link(model_empty)
		elif resource_type == "WheelGraphicsSpec":
			wheelgraphicsspec_collection.objects.link(model_empty)
		else:
			main_collection.objects.link(model_empty)
		
		instance_properties = instances[i][1]
		is_shattered_glass = False
		
		model_empty["object_index"] = i
		if resource_type == "InstanceList":
			if i < (len(instances) - len(instances_props)):
				mpModel, mi16BackdropZoneID, mu16Pad, mu32Pad, mfMaxVisibleDistanceSquared, mTransform, is_always_loaded = instance_properties
				
				model_empty["Model"] = mpModel
				model_empty["BackdropZoneID"] = mi16BackdropZoneID
				model_empty["mu16Pad"] = mu16Pad
				model_empty["mu32Pad"] = mu32Pad
				model_empty["MaxVisibleDistanceSquared"] = mfMaxVisibleDistanceSquared
				model_empty["is_always_loaded"] = is_always_loaded
			else:
				muTypeId, muInstanceID, muAlternativeType, mn8RotSpeed, mn8MAngle, mTransform, prop_type, muFlags, muPartId = instance_properties
				
				model_empty["TypeId"] = muTypeId
				model_empty["Flags"] = muFlags
				model_empty["InstanceID"] = muInstanceID
				model_empty["AlternativeType"] = muAlternativeType
				model_empty["RotSpeed"] = mn8RotSpeed
				model_empty["MAngle"] = mn8MAngle
				model_empty["prop_type"] = prop_type
				if prop_type == "prop":
					model_empty["Parts"] = muPartId
				elif prop_type == "prop_part":
					model_empty["PartId"] = muPartId
		
		elif resource_type == "GraphicsSpec":
			is_shattered_glass = instances[i][-1]
			if is_shattered_glass == False:
				mTransform, part_volume_id = instance_properties
				model_empty["part_volume_id"] = part_volume_id
			
			elif is_shattered_glass == True:
				shattered_glass = instance_properties[0]
				mpModel, muBodyPartIndex, muBodyPartType = shattered_glass
				
				model_empty["Model"] = mpModel
				model_empty["BodyPartIndex"] = muBodyPartIndex
				model_empty["BodyPartType"] = muBodyPartType
				mTransform = instances[muBodyPartIndex][1][0]
			
			model_empty["is_shattered_glass"] = is_shattered_glass
			model_empty.empty_display_size = 0.5
		
		elif resource_type == "WheelGraphicsSpec":
			mTransform = instance_properties[0]
			is_caliper = instances[i][-1]
			model_empty["is_caliper"] = is_caliper
			model_empty.empty_display_size = 0.5
		
		elif resource_type == "GraphicsStub":
			if i < (len(instances) - len(instances_wheel)):
				is_shattered_glass = instances[i][-1]
				if is_shattered_glass == False:
					mTransform, part_volume_id = instance_properties
					model_empty["part_volume_id"] = part_volume_id
				
				elif is_shattered_glass == True:
					shattered_glass = instance_properties[0]
					mpModel, muBodyPartIndex, muBodyPartType = shattered_glass
					
					model_empty["Model"] = mpModel
					model_empty["BodyPartIndex"] = muBodyPartIndex
					model_empty["BodyPartType"] = muBodyPartType
					mTransform = instances[muBodyPartIndex][1][0]
				
				model_empty["is_shattered_glass"] = is_shattered_glass
			else:
				mTransform = instance_properties[0]
				is_caliper = instances[i][-1]
				model_empty["is_caliper"] = is_caliper
			model_empty.empty_display_size = 0.5
		
		model = models[mModelId]
		
		model_properties = model[1][1]
		miGameExplorerIndex = model_properties[3]
		mu8Flags = model_properties[5]
		mu8NumStates = model_properties[6]
		mu8VersionNumber = model_properties[7]
		
		model_empty["GameExplorerIndex"] = miGameExplorerIndex
		model_empty["Flags"] = mu8Flags
		model_empty["NumStates"] = mu8NumStates
		model_empty["is_shared_asset"] = model[2]
		
		for renderable_info in model[1][0]:
			mRenderableId = renderable_info[0]
			if len(renderable_info) == 2 and (mRenderableId not in renderable_already_scene):
				renderable_object = bpy.context.scene.objects[mRenderableId]
				
				renderable_index = renderable_info[1][0]
				lod_distance = renderable_info[1][1]
				renderable_object["renderable_index"] = renderable_index		#different models could use the same renderable with different properties
				renderable_object["lod_distance"] = lod_distance
				
				renderable_object.parent = model_empty
				renderable_info.append("copied")
				#if renderable_index > 0:
				#	renderable_object.hide_set(True)
			else:
				src_renderable_object = bpy.data.objects.get(mRenderableId)
				src_renderable_mesh = bpy.data.meshes.get(mRenderableId)
				renderable_object = bpy.data.objects.new(mRenderableId, src_renderable_mesh)
				renderable_object.parent = model_empty
				main_collection.objects.link(renderable_object)
				
				renderable_object["renderable_index"] = src_renderable_object["renderable_index"]
				renderable_object["lod_distance"] = src_renderable_object["lod_distance"]
				renderable_object["is_shared_asset"] = src_renderable_object["is_shared_asset"]
				renderable_object["flags"] = src_renderable_object["flags"]
				renderable_object["object_center"] = src_renderable_object["object_center"]
				renderable_object["object_radius"] = src_renderable_object["object_radius"]
			
			if resource_type == "InstanceList":
				hide_status = renderable_object.hide_get()
				renderable_object.users_collection[0].objects.unlink(renderable_object)
				if i < (len(instances) - len(instances_props)):
					instancelist_collection.objects.link(renderable_object)
				else:
					prop_collection.objects.link(renderable_object)
					renderable_index = renderable_info[1][0]
					if renderable_index == 0:
						bbox_y = [point[1] for point in renderable_object.bound_box]
						mTransform[1][3] -= min(bbox_y)
				renderable_object.hide_set(hide_status)
			
			elif resource_type == "GraphicsStub":
				hide_status = renderable_object.hide_get()
				renderable_object.users_collection[0].objects.unlink(renderable_object)
				if i < (len(instances) - len(instances_wheel)):
					graphicsspec_collection.objects.link(renderable_object)
				else:
					wheelgraphicsspec_collection.objects.link(renderable_object)
				renderable_object.hide_set(hide_status)
			
			elif resource_type == "GraphicsSpec":
				hide_status = renderable_object.hide_get()
				renderable_object.users_collection[0].objects.unlink(renderable_object)
				graphicsspec_collection.objects.link(renderable_object)
				renderable_object.hide_set(hide_status)
			
			elif resource_type == "WheelGraphicsSpec":
				hide_status = renderable_object.hide_get()
				renderable_object.users_collection[0].objects.unlink(renderable_object)
				wheelgraphicsspec_collection.objects.link(renderable_object)
				renderable_object.hide_set(hide_status)
		
		model_empty.matrix_world = m @ mTransform
		#model_empty.matrix_world = Matrix((mTransform[2], mTransform[0], mTransform[1], mTransform[3]))
		# loss of precision on matrix_world: https://developer.blender.org/T30706
	
	if resource_type == "InstanceList":
		staticsoundmap_info_emitter, instances_emitter = emitter_data
		mfSubRegionSize, miNumSubRegionsX, miNumSubRegionsZ, meRootType = staticsoundmap_info_emitter
		StaticSoundEntities, mSubRegions_first, mSubRegions_count = instances_emitter
		
		staticsoundmap_emitter_collection["SubRegionSize"] = mfSubRegionSize
		staticsoundmap_emitter_collection["NumSubRegionsX"] = miNumSubRegionsX
		staticsoundmap_emitter_collection["NumSubRegionsZ"] = miNumSubRegionsZ
		staticsoundmap_emitter_collection["RootType"] = meRootType
		staticsoundmap_emitter_collection["SubRegions_first"] = mSubRegions_first
		staticsoundmap_emitter_collection["SubRegions_count"] = mSubRegions_count
		
		for i, StaticSoundEntity in enumerate(StaticSoundEntities):
			staticsound_object_name = "Sound_%03d_%s.%03d" % (i, "Emitter", track_unit_number)
			sound_empty = bpy.data.objects.new(staticsound_object_name, None)
			staticsoundmap_emitter_collection.objects.link(sound_empty)
			
			mPosPlus, unk = StaticSoundEntity
			mTransform = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [*mPosPlus, 1.0]]).transposed()
			sound_empty.matrix_world = m @ mTransform
			sound_empty["unk"] = unk
		
		staticsoundmap_info_passby, instances_passby = passby_data
		mfSubRegionSize, miNumSubRegionsX, miNumSubRegionsZ, meRootType = staticsoundmap_info_passby
		StaticSoundEntities, mSubRegions_first, mSubRegions_count = instances_passby
		
		staticsoundmap_passby_collection["SubRegionSize"] = mfSubRegionSize
		staticsoundmap_passby_collection["NumSubRegionsX"] = miNumSubRegionsX
		staticsoundmap_passby_collection["NumSubRegionsZ"] = miNumSubRegionsZ
		staticsoundmap_passby_collection["RootType"] = meRootType
		staticsoundmap_passby_collection["SubRegions_first"] = mSubRegions_first
		staticsoundmap_passby_collection["SubRegions_count"] = mSubRegions_count
		
		for i, StaticSoundEntity in enumerate(StaticSoundEntities):
			staticsound_object_name = "Sound_%03d_%s.%03d" % (i, "Passby", track_unit_number)
			sound_empty = bpy.data.objects.new(staticsound_object_name, None)
			staticsoundmap_passby_collection.objects.link(sound_empty)
			
			mPosPlus, unk = StaticSoundEntity
			mTransform = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [*mPosPlus, 1.0]]).transposed()
			sound_empty.matrix_world = m @ mTransform
			sound_empty["unk"] = unk
	
	elif resource_type == "StreamedDeformationSpec":
		wheel_tagpoints = []
		for i, WheelSpec in enumerate(WheelSpecs):
			wheelspec_object_name = "WheelSpec_%d.%s" % (i, vehicle_name)
			wheelspec_empty = bpy.data.objects.new(wheelspec_object_name, None)
			wheelspec_empty.empty_display_type = 'SPHERE'
			wheelsspec_collection.objects.link(wheelspec_empty)
			
			mPosition, mScale, TagPointIndex, WheelSide = WheelSpec
			mTransform = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], mPosition]).transposed()
			mTransform.translation -= mCarModelSpaceToHandlingBodySpaceTransform.translation
			
			wheelspec_empty.empty_display_size = mScale[1]
			wheelspec_empty.matrix_world = m @ mTransform
			wheelspec_empty.scale = mScale[:3]
			wheelspec_empty["TagPointIndex"] = TagPointIndex
			wheelspec_empty["WheelSide"] = WheelSide
			
			mInitialPosition, mfWeightA, mfWeightB, mfDetachThresholdSquared, miDeformationSensorA, miDeformationSensorB, miJointIndex, mbSkinnedPoint = TagPointSpecs[TagPointIndex]
			wheelspec_empty["WeightA"] = mfWeightA
			wheelspec_empty["WeightB"] = mfWeightB
			wheelspec_empty["DetachThresholdSquared"] = mfDetachThresholdSquared
			wheelspec_empty["DeformationSensorA"] = miDeformationSensorA
			wheelspec_empty["DeformationSensorB"] = miDeformationSensorB
			wheelspec_empty["JointIndex"] = miJointIndex
			wheelspec_empty["SkinnedPoint"] = mbSkinnedPoint
			
			wheel_tagpoints.append(TagPointIndex)
		
		for i, sensor in enumerate(SensorSpecs):
			mu8SceneIndex = sensor[4]
			sensor_object_name = "SensorSpec_%d.%s" % (mu8SceneIndex-1, vehicle_name)
			sensor_empty = bpy.data.objects.new(sensor_object_name, None)
			sensor_empty.empty_display_type = 'CUBE'
			sensorspecs_collection.objects.link(sensor_empty)
			
			mInitialOffset, maDirectionParams, mfRadius, maNextSensor, mu8SceneIndex, mu8AbsorbtionLevel, mau8NextBoundarySensor = sensor
			
			mLocatorMatrix = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [*mInitialOffset, 1.0]]).transposed()
			mLocatorMatrix.translation -= mCarModelSpaceToHandlingBodySpaceTransform.translation
			
			sensor_empty.empty_display_size = mfRadius
			sensor_empty.matrix_world = m @ mLocatorMatrix
			sensor_empty["DirectionParams"] = maDirectionParams
			sensor_empty["Radius"] = mfRadius
			sensor_empty["NextSensor"] = maNextSensor
			sensor_empty["AbsorbtionLevel"] = mu8AbsorbtionLevel
			sensor_empty["NextBoundarySensor"] = mau8NextBoundarySensor
		
		for i, tag in enumerate(TagPointSpecs):
			if i in wheel_tagpoints:
				continue
			tag_object_name = "TagPointSpec_%d.%s" % (i, vehicle_name)
			tag_empty = bpy.data.objects.new(tag_object_name, None)
			tag_empty.empty_display_type = 'SPHERE'
			tagpointspecs_collection.objects.link(tag_empty)
			
			mInitialPosition, mfWeightA, mfWeightB, mfDetachThresholdSquared, miDeformationSensorA, miDeformationSensorB, miJointIndex, mbSkinnedPoint = tag
			
			mLocatorMatrix = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [*mInitialPosition, 1.0]]).transposed()
			mLocatorMatrix.translation -= mCarModelSpaceToHandlingBodySpaceTransform.translation
			
			tag_empty.empty_display_size = 0.02
			tag_empty.matrix_world = m @ mLocatorMatrix
			tag_empty["WeightA"] = mfWeightA
			tag_empty["WeightB"] = mfWeightB
			tag_empty["DetachThresholdSquared"] = mfDetachThresholdSquared
			tag_empty["DeformationSensorA"] = miDeformationSensorA
			tag_empty["DeformationSensorB"] = miDeformationSensorB
			tag_empty["JointIndex"] = miJointIndex
			tag_empty["SkinnedPoint"] = mbSkinnedPoint
		
		for i, driven in enumerate(DrivenPoints):
			drive_object_name = "DrivenPoint_%d.%s" % (i + len(TagPointSpecs) - 4, vehicle_name) # maybe not always -4 (minus four wheels, maybe look at minus number mbSkinnedPoint)
			driven_empty = bpy.data.objects.new(drive_object_name, None)
			driven_empty.empty_display_type = 'CONE'
			drivenpoints_collection.objects.link(driven_empty)
			
			mInitialPos, miTagPointIndexA, miTagPointIndexB = driven
			
			mLocatorMatrix = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [*mInitialPos, 1.0]]).transposed()
			mLocatorMatrix.translation -= mCarModelSpaceToHandlingBodySpaceTransform.translation
			
			driven_empty.empty_display_size = 0.02
			driven_empty.matrix_world = m @ mLocatorMatrix
			driven_empty["TagPointIndexA"] = miTagPointIndexA
			driven_empty["TagPointIndexB"] = miTagPointIndexB
		
		for i, tag in enumerate(GenericTags):
			tag_object_name = "GenericTag_%d.%s" % (i, vehicle_name)
			tag_empty = bpy.data.objects.new(tag_object_name, None)
			generictags_collection.objects.link(tag_empty)
			
			index, mLocatorMatrix, meTagPointType, miIkPartIndex, mu8SkinPoint = tag
			mLocatorMatrix.translation -= mCarModelSpaceToHandlingBodySpaceTransform.translation
			
			tag_empty.empty_display_size = 0.5
			tag_empty.matrix_world = m @ mLocatorMatrix
			tag_empty["TagPointType"] = meTagPointType
			tag_empty["IkPartIndex"] = miIkPartIndex
			tag_empty["SkinPoint"] = mu8SkinPoint
		
		for i, tag in enumerate(CameraTags):
			tag_object_name = "CameraTag_%d.%s" % (i, vehicle_name)
			camera_data = bpy.data.cameras.new(name = tag_object_name)
			tag_empty = bpy.data.objects.new(tag_object_name, camera_data)
			cameratags_collection.objects.link(tag_empty)
			
			index, mLocatorMatrix, meTagPointType, miIkPartIndex, mu8SkinPoint = tag
			mLocatorMatrix.translation -= mCarModelSpaceToHandlingBodySpaceTransform.translation
			
			camera_data.display_size = 0.25
			tag_empty.matrix_world = m @ mLocatorMatrix
			tag_empty.rotation_euler[2] = -math.pi*0.5
			tag_empty["TagPointType"] = meTagPointType
			tag_empty["IkPartIndex"] = miIkPartIndex
			tag_empty["SkinPoint"] = mu8SkinPoint
		
		for i, tag in enumerate(LightTags):
			tag_object_name = "LightTag_%d.%s" % (i, vehicle_name)
			tag_empty = bpy.data.objects.new(tag_object_name, None)
			lighttags_collection.objects.link(tag_empty)
			
			index, mLocatorMatrix, meTagPointType, miIkPartIndex, mu8SkinPoint = tag
			mLocatorMatrix.translation -= mCarModelSpaceToHandlingBodySpaceTransform.translation
			
			tag_empty.empty_display_size = 0.5
			tag_empty.matrix_world = m @ mLocatorMatrix
			tag_empty["TagPointType"] = meTagPointType
			tag_empty["IkPartIndex"] = miIkPartIndex
			tag_empty["SkinPoint"] = mu8SkinPoint
		
		saved_cursor_location = bpy.context.scene.cursor.location
		for i, IKPartData in enumerate(IKParts):
			IKPart_object_name = "IKPart_%d.%s" % (i, vehicle_name)
			IKPart_empty = bpy.data.objects.new(IKPart_object_name, None)
			ikparts_collection.objects.link(IKPart_empty)
			
			mGraphicsTransform, mBBoxSkinData, mJointSpecs, miPartGraphics, miStartIndexOfDrivenPoints, miNumberOfDrivenPoints, miStartIndexOfTagPoints, miNumberOfTagPoints, mePartType = IKPartData
			
			IKPart_empty.empty_display_size = 0.1
			IKPart_empty.matrix_world = m @ mGraphicsTransform
			IKPart_empty["PartGraphics"] = miPartGraphics
			IKPart_empty["StartIndexOfDrivenPoints"] = miStartIndexOfDrivenPoints
			IKPart_empty["NumberOfDrivenPoints"] = miNumberOfDrivenPoints
			IKPart_empty["StartIndexOfTagPoints"] = miStartIndexOfTagPoints
			IKPart_empty["NumberOfTagPoints"] = miNumberOfTagPoints
			IKPart_empty["PartType"] = mePartType
			
			BBoxSkin_object_name = "BBoxSkin_IKPart_%d.%s" % (i, vehicle_name)
			BBoxSkin_object = create_bbox(BBoxSkin_object_name, mBBoxSkinData)
			BBoxSkin_object["Orientation_0"] = mBBoxSkinData[0][0]
			BBoxSkin_object["Orientation_1"] = mBBoxSkinData[0][1]
			BBoxSkin_object["Orientation_2"] = mBBoxSkinData[0][2]
			BBoxSkin_object["Orientation_3"] = mBBoxSkinData[0][3]
			#BBoxSkin_object.parent = IKPart_empty
			ikparts_collection.objects.link(BBoxSkin_object)
			
			#BBoxSkin_object.select_set(True)
			#bpy.context.scene.cursor.location = mBBoxSkinData[2][0][:3]
			#bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
			#BBoxSkin_object.select_set(False)
			BBoxSkin_object.parent = IKPart_empty
			
			for j, mJointSpec in enumerate(mJointSpecs):
				mJointPosition, mJointAxis, mJointDefaultDirection, mfMaxJointAngle, mfJointDetachThreshold, meJointType = mJointSpec
				
				JointSpec_object_name = "JointSpec_%d_IKPart_%d.%s" % (j, i, vehicle_name)
				JointSpec_empty = bpy.data.objects.new(JointSpec_object_name, None)
				
				mJointMatrix = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], mJointPosition]).transposed()
				mJointMatrix.translation -= mCarModelSpaceToHandlingBodySpaceTransform.translation
				
				JointSpec_empty.empty_display_size = 0.1
				JointSpec_empty.matrix_world = m @ mJointMatrix
				JointSpec_empty["JointAxis"] = mJointAxis
				JointSpec_empty["JointDefaultDirection"] = mJointDefaultDirection
				JointSpec_empty["MaxJointAngle"] = mfMaxJointAngle
				JointSpec_empty["JointDetachThreshold"] = mfJointDetachThreshold
				JointSpec_empty["JointType"] = meJointType
				
				JointSpec_empty.parent = IKPart_empty
				JointSpec_empty.matrix_parent_inverse = IKPart_empty.matrix_world.inverted()
				
				ikparts_collection.objects.link(JointSpec_empty)
				
		
		bpy.context.scene.cursor.location = saved_cursor_location
		
		for i, GlassPaneData in enumerate(GlassPanes):
			glass_object_name = "GlassPane_%d.%s" % (i, vehicle_name)
			glass_empty = bpy.data.objects.new(glass_object_name, None)
			glasspanes_collection.objects.link(glass_empty)
			
			glasspane_0x00, glasspane_0x10, glasspane_0x50, glasspane_0x58, glasspane_0x5C, glasspane_0x5E, glasspane_0x60, mePartType = GlassPaneData
			
			#mLocatorMatrix = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [glasspane_0x00[0], glasspane_0x00[1], glasspane_0x00[2], 1.0]]).transposed()
			mLocatorMatrix = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]).transposed()
			##mLocatorMatrix.translation[0] += mCarModelSpaceToHandlingBodySpaceTransform.translation[0]
			#mLocatorMatrix.translation[1] += mCarModelSpaceToHandlingBodySpaceTransform.translation[2]
			#mLocatorMatrix.translation[2] += mCarModelSpaceToHandlingBodySpaceTransform.translation[1]
			
			glass_empty.empty_display_size = 0.1
			glass_empty.matrix_world = m @ mLocatorMatrix
			glass_empty["PartType"] = mePartType
			glass_empty["glasspane_0x00"] = glasspane_0x00
			glass_empty["glasspane_0x10"] = glasspane_0x10[0]
			glass_empty["glasspane_0x20"] = glasspane_0x10[1]
			glass_empty["glasspane_0x30"] = glasspane_0x10[2]
			glass_empty["glasspane_0x40"] = glasspane_0x10[3]
			glass_empty["TagPointIndices"] = glasspane_0x50
			glass_empty["glasspane_0x58"] = glasspane_0x58
			glass_empty["glasspane_0x5C"] = glasspane_0x5C
			glass_empty["DeformationSensorA"] = glasspane_0x5E
			glass_empty["DeformationSensorB"] = glasspane_0x60
			
			#glass_object = create_pane(glass_object_name, GlassPaneData)
			#glasspanes_collection.objects.link(glass_object)
	
	elif resource_type == "PolygonSoupList":
		for collision in world_collision:
			track_unit_number, mPolygonSoupList, PolygonSoups, polygonsouplist_collection = collision
			for i, PolygonSoup in enumerate(PolygonSoups):
				polygonsoup_empty_name = "PolygonSoup_%03d.%03d" % (i, track_unit_number)
				polygonsoup_empty = bpy.data.objects.new(polygonsoup_empty_name, None)
				polygonsouplist_collection.objects.link(polygonsoup_empty)
				
				maiVertexOffsets, mfComprGranularity, PolygonSoupVertices, PolygonSoupPolygons = PolygonSoup
				
				polygonsoup_object_name = "PolygonSoupMesh_%03d.%03d" % (i, track_unit_number)
				polygonsoup_object = create_polygonsoup(polygonsoup_object_name, PolygonSoupVertices, PolygonSoupPolygons)
				polygonsoup_object.parent = polygonsoup_empty
				polygonsouplist_collection.objects.link(polygonsoup_object)
				
				mTransform = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [*maiVertexOffsets, 1.0]]).transposed()
				mTransform *= mfComprGranularity
				polygonsoup_empty.matrix_world = m @ mTransform
	
	elapsed_time = time.time() - importing_time
	print("... %.4fs" % elapsed_time)
	
	## Adjusting scene
	for window in bpy.context.window_manager.windows:
		for area in window.screen.areas:
			if area.type == 'VIEW_3D':
				for space in area.spaces:
					if space.type == 'VIEW_3D':
						if resource_type == "PolygonSoupList":
							space.shading.type = 'SOLID'
						else:
							space.shading.type = 'MATERIAL'
						space.clip_end = 100000
				region = next(region for region in area.regions if region.type == 'WINDOW')
				override = bpy.context.copy()
				override['area'] = area
				override['region'] = region
				bpy.ops.view3d.view_all(override, use_all_regions=False, center=False)
	
	if is_bundle == True:
		temp_dir.cleanup()
	
	print("Finished")
	elapsed_time = time.time() - start_time
	print("Elapsed time: %.4fs" % elapsed_time)
	return {'FINISHED'}


def read_instancelist(instancelist_path): #ok
	mpaInstances = muArraySize = muNumInstances = muVersionNumber = 0
	instances = []
	with open(instancelist_path, "rb") as f:
		mpaInstances, muArraySize, muNumInstances, muVersionNumber = struct.unpack(">4I", f.read(0x10))
		for i in range(0, muArraySize):
			f.seek(mpaInstances + 0x50*i, 0)
			mpModel, mi16BackdropZoneID, mu16Pad, mu32Pad, mfMaxVisibleDistanceSquared = struct.unpack(">ihHIf", f.read(0x10))
			mTransform = [[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))]]
			mTransform = Matrix(mTransform)
			mTransform = mTransform.transposed()
			
			f.seek(mpaInstances + 0x50*muArraySize + 0x10*i, 0)
			_ = struct.unpack(">i", f.read(0x4))[0]
			mResourceId = bytes_to_id(f.read(0x4))
			
			is_always_loaded = True
			if i >= muNumInstances:
				is_always_loaded = False
			instance_properties = [mpModel, mi16BackdropZoneID, mu16Pad, mu32Pad, mfMaxVisibleDistanceSquared, mTransform, is_always_loaded]
			instances.append([mResourceId, instance_properties])
	
	return (mpaInstances, muArraySize, muNumInstances, muVersionNumber, instances)


def read_propgraphicslist(propgraphicslist_path): #ok
	prop_info = []
	prop_part_info = []
	with open(propgraphicslist_path, "rb") as f:
		muSizeInBytes = struct.unpack(">I", f.read(0x4))[0]
		muZoneNumber = struct.unpack(">I", f.read(0x4))[0]
		muNumberOfPropModels = struct.unpack(">I", f.read(0x4))[0]
		muNumberOfPropPartModels = struct.unpack("<I", f.read(0x4))[0]
		mpaPropGraphics = struct.unpack(">i", f.read(0x4))[0]
		mpaPropPartGraphics = struct.unpack(">i", f.read(0x4))[0]
		
		if muNumberOfPropModels > 0:
			f.seek(mpaPropGraphics, 0)
		prop_graphics = []
		for i in range(0, muNumberOfPropModels):
			muTypeId, mpPropModel, mpParts = struct.unpack(">Iii", f.read(0xC))
			prop_graphics.append([muTypeId, mpPropModel, mpParts])
		
		if muNumberOfPropPartModels > 0:
			f.seek(mpaPropPartGraphics, 0)
		prop_part_graphics = []
		prop_part_model_indices = {}
		for i in range(0, muNumberOfPropPartModels):
			mpParts = f.tell()
			muTypeId, muPartId, mpPropModel = struct.unpack("<IIi", f.read(0xC))
			prop_part_graphics.append([muTypeId, muPartId, mpPropModel])
			prop_part_model_indices[mpParts] = i
		
		padding = calculate_padding(f.tell(), 0x10)
		f.seek(padding, 1)
		
		for i in range(0, muNumberOfPropModels):
			_ = struct.unpack(">i", f.read(0x4))[0]
			mResourceId = bytes_to_id(f.read(0x4))
			muOffset = struct.unpack(">I", f.read(0x4))[0]
			padding = struct.unpack(">i", f.read(0x4))[0]
			
			try:
				prop_part_model_index = prop_part_model_indices[prop_graphics[i][2]]
			except:
				prop_part_model_index = -1
			
			prop_info.append([mResourceId, prop_graphics[i][0], prop_part_model_index, "prop"])
		
		for i in range(0, muNumberOfPropPartModels):
			_ = struct.unpack(">i", f.read(0x4))[0]
			mResourceId = bytes_to_id(f.read(0x4))
			muOffset = struct.unpack(">I", f.read(0x4))[0]
			padding = struct.unpack(">i", f.read(0x4))[0]
			
			prop_part_info.append([mResourceId, prop_part_graphics[i][0], prop_part_graphics[i][1], "prop_part"])
		
	return (prop_info, prop_part_info)


def read_propinstancedata(propinstancedata_path, prop_info, prop_part_info): #ok
	instances = []
	unk1s = []
	with open(propinstancedata_path, "rb") as f:
		unk1_pointer = struct.unpack(">I", f.read(0x4))[0]
		num_unk1s = struct.unpack("<I", f.read(0x4))[0]
		mpaPropInstanceData = struct.unpack(">I", f.read(0x4))[0]
		data_length = struct.unpack(">I", f.read(0x4))[0]
		muNumberOfPropInstanceDataPlusPropParts = struct.unpack(">I", f.read(0x4))[0]
		muNumberOfPropInstanceData = struct.unpack(">I", f.read(0x4))[0]
		muZoneNumber = struct.unpack(">I", f.read(0x4))[0]
		
		f.seek(mpaPropInstanceData, 0)
		for i in range(0, muNumberOfPropInstanceData):
			mWorldTransform = [[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))]]
			mWorldTransform = Matrix(mWorldTransform)
			mWorldTransform = mWorldTransform.transposed()
			
			#muTypeIdAndFlags = struct.unpack(">I", f.read(0x4))[0]
			muFlags = struct.unpack(">B", f.read(0x1))[0]
			_ = struct.unpack(">B", f.read(0x1))[0]
			muTypeId = struct.unpack(">H", f.read(0x2))[0]
			muInstanceID = struct.unpack(">I", f.read(0x4))[0]
			muAlternativeType = struct.unpack(">H", f.read(0x2))[0]		# if different than 0xFFFF, the model will be replaced after broken
			mn8RotSpeed = struct.unpack(">b", f.read(0x1))[0]
			mn8MaxAngle = struct.unpack(">B", f.read(0x1))[0]
			mn8MinAngle = struct.unpack(">B", f.read(0x1))[0]
			mau8Padding = struct.unpack(">BBB", f.read(0x3))
			
			for prop in prop_info:
				if muTypeId == prop[1]:
					mResourceId = prop[0]
					prop_part_model_index = prop[2]
					if prop_part_model_index == -1:
						mParts = 0
					else:
						mParts = prop_part_info[prop_part_model_index][1]
					break
			else:
				print("WARNING: mResourceId of prop %s not found. Ignoring it." % muTypeId)
				continue
			instance_properties = [muTypeId, muInstanceID, muAlternativeType, mn8RotSpeed, [mn8MaxAngle, mn8MinAngle], mWorldTransform, prop[3], muFlags, mParts]
			instances.append([mResourceId, instance_properties])
			
			if prop_part_model_index != -1:
				mResourceId, muTypeId_, muPartId, prop_type = prop_part_info[prop_part_model_index]
				if muTypeId_ != muTypeId:
					continue
				instance_properties = [muTypeId_, muInstanceID, muAlternativeType, mn8RotSpeed, [mn8MaxAngle, mn8MinAngle], mWorldTransform.copy(), prop_type, muFlags, muPartId]
				instances.append([mResourceId, instance_properties])
				for j in range(prop_part_model_index + 1, len(prop_part_info)):
					if prop_part_info[j][1] == muTypeId:
						mResourceId, muTypeId_, muPartId, prop_type = prop_part_info[j]
						instance_properties = [muTypeId_, muInstanceID, muAlternativeType, mn8RotSpeed, [mn8MaxAngle, mn8MinAngle], mWorldTransform.copy(), prop_type, muFlags, muPartId]
						instances.append([mResourceId, instance_properties])
					else:
						break
			
			if muAlternativeType != 0xFFFF:
				prop_type = "prop_alternative"
				for prop in prop_info:
					if muAlternativeType == prop[1]:
						mResourceId = prop[0]
						prop_part_model_index = prop[2]
						if prop_part_model_index == -1:
							mParts = 0
						else:
							mParts = prop_part_info[prop_part_model_index][1]
						break
				else:
					print("WARNING: mResourceId of prop %s not found. Ignoring it." % muAlternativeType)
					continue
				instance_properties = [muAlternativeType, muInstanceID, 0xFFFF, mn8RotSpeed, [mn8MaxAngle, mn8MinAngle], mWorldTransform.copy(), prop_type, muFlags, mParts]
				instances.append([mResourceId, instance_properties])
				
				if prop_part_model_index != -1:
					mResourceId, muTypeId_, muPartId, prop_type = prop_part_info[prop_part_model_index]
					if muTypeId_ != muAlternativeType:
						continue
					instance_properties = [muTypeId_, muInstanceID, 0xFFFF, mn8RotSpeed, [mn8MaxAngle, mn8MinAngle], mWorldTransform.copy(), prop_type, muFlags, muPartId]
					instances.append([mResourceId, instance_properties])
					for j in range(prop_part_model_index + 1, len(prop_part_info)):
						if prop_part_info[j][1] == muAlternativeType:
							mResourceId, muTypeId_, muPartId, prop_type = prop_part_info[j]
							instance_properties = [muTypeId_, muInstanceID, 0xFFFF, mn8RotSpeed, [mn8MaxAngle, mn8MinAngle], mWorldTransform.copy(), prop_type, muFlags, muPartId]
							instances.append([mResourceId, instance_properties])
						else:
							break
		
		f.seek(unk1_pointer, 0)
		for i in range(0, num_unk1s):
			unk1 = struct.unpack(">HHHHHH", f.read(0xC))
			unk1s.append([*unk1[:2], *unk1[3:]])
	
	return (instances, unk1s)


def read_staticsoundmap(staticsoundmap_path): #ok
	staticsoundmap_info = []
	instances = []
	with open(staticsoundmap_path, "rb") as f:
		StaticSoundEntities = []
		mSubRegions_first = []
		mSubRegions_count = []
		
		mMin = struct.unpack(">ff", f.read(0x8))
		padding = f.read(0x8)
		mMax = struct.unpack(">ff", f.read(0x8))
		padding = f.read(0x8)
		mfSubRegionSize = struct.unpack(">f", f.read(0x4))[0]
		mpSubRegions = struct.unpack(">I", f.read(0x4))[0]
		miNumSubRegionsX = struct.unpack(">i", f.read(0x4))[0]
		miNumSubRegionsZ = struct.unpack(">i", f.read(0x4))[0]
		mpEntities = struct.unpack(">I", f.read(0x4))[0]
		miNumEntities = struct.unpack(">i", f.read(0x4))[0]
		meRootType = struct.unpack(">i", f.read(0x4))[0] #it seems unused
		
		miNumSubRegions = miNumSubRegionsX*miNumSubRegionsZ
		
		f.seek(mpEntities, 0)
		for i in range(0, miNumEntities):
			mPosPlus = struct.unpack(">fff", f.read(0xC))
			unk = struct.unpack(">HH", f.read(0x4))
			unk = [unk[1], unk[0]]
			
			StaticSoundEntities.append([mPosPlus, unk])
		
		f.seek(mpSubRegions, 0)
		for i in range(0, miNumSubRegions):
			mi16First = struct.unpack(">h", f.read(0x2))[0]
			mi16Count = struct.unpack(">h", f.read(0x2))[0]
			
			mSubRegions_first.append(mi16First)
			mSubRegions_count.append(mi16Count)
		
		staticsoundmap_info = [mfSubRegionSize, miNumSubRegionsX, miNumSubRegionsZ, meRootType]
		instances = [StaticSoundEntities, mSubRegions_first, mSubRegions_count]
		
	return (staticsoundmap_info, instances)


def read_polygonsouplist(polygonsouplist_path): #ok
	PolygonSoups = []
	with open(polygonsouplist_path, "rb") as f:
		mMin = struct.unpack(">3f", f.read(0xC))
		mMin_w = struct.unpack(">f", f.read(0x4))[0]
		mMax = struct.unpack(">3f", f.read(0xC))
		mMax_w = struct.unpack(">f", f.read(0x4))[0]
		mpapPolySoups = struct.unpack(">I", f.read(0x4))[0]
		mpaPolySoupBoxes = struct.unpack(">I", f.read(0x4))[0]
		miNumPolySoups = struct.unpack(">i", f.read(0x4))[0]
		miDataSize = struct.unpack(">i", f.read(0x4))[0]
		
		mpPolySoups = []
		f.seek(mpapPolySoups, 0)
		mpPolySoups = struct.unpack(">%dI" % miNumPolySoups, f.read(0x4*miNumPolySoups))
		
		PolySoupBoxes = []
		f.seek(mpaPolySoupBoxes, 0)
		for i in range(0, miNumPolySoups):
			f.seek(int(mpaPolySoupBoxes + 0x70*(i//4) + 0x4*(i%4)), 0)
			mAabbMinX = struct.unpack(">f", f.read(0x4))[0]
			f.seek(0xC, 1)
			mAabbMinY = struct.unpack(">f", f.read(0x4))[0]
			f.seek(0xC, 1)
			mAabbMinZ = struct.unpack(">f", f.read(0x4))[0]
			f.seek(0xC, 1)
			mAabbMaxX = struct.unpack(">f", f.read(0x4))[0]
			f.seek(0xC, 1)
			mAabbMaxY = struct.unpack(">f", f.read(0x4))[0]
			f.seek(0xC, 1)
			mAabbMaxZ = struct.unpack(">f", f.read(0x4))[0]
			f.seek(0xC, 1)
			mValidMasks = struct.unpack(">i", f.read(0x4))[0]
			PolySoupBoxes.append([[mAabbMinX, mAabbMinY, mAabbMinZ], [mAabbMaxX, mAabbMaxY, mAabbMaxZ], mValidMasks])
		
		for i in range(0, miNumPolySoups):
			f.seek(mpPolySoups[i], 0)
			maiVertexOffsets = struct.unpack(">3i", f.read(0xC))
			mfComprGranularity = struct.unpack(">f", f.read(0x4))[0]
			mpaPolygons = struct.unpack(">I", f.read(0x4))[0]
			mpaVertices = struct.unpack(">I", f.read(0x4))[0]
			mu16DataSize = struct.unpack(">H", f.read(0x2))[0]
			mu8TotalNumPolys = struct.unpack(">B", f.read(0x1))[0]
			mu8NumQuads = struct.unpack(">B", f.read(0x1))[0]
			mu8NumVertices = struct.unpack(">B", f.read(0x1))[0]
			padding = f.read(0x3)
			
			PolygonSoupVertices = []
			f.seek(mpaVertices, 0)
			for j in range(0, mu8NumVertices):
				mu16X, mu16Y, mu16Z = struct.unpack(">HHH", f.read(0x6))
				PolygonSoupVertex = [mu16X, mu16Y, mu16Z]
				PolygonSoupVertices.append(PolygonSoupVertex)
			
			PolygonSoupPolygons = []
			f.seek(mpaPolygons, 0)
			for j in range(0, mu8NumQuads):
				mu16CollisionTag_part1 = struct.unpack(">H", f.read(0x2))[0]
				mu16CollisionTag_part0 = struct.unpack(">H", f.read(0x2))[0]
				mau8VertexIndices = struct.unpack(">4B", f.read(0x4))
				mau8EdgeCosines = struct.unpack(">4B", f.read(0x4))
				PolygonSoupPolygons.append([[mu16CollisionTag_part0, mu16CollisionTag_part1], mau8VertexIndices, mau8EdgeCosines])
			
			for j in range(mu8NumQuads, mu8TotalNumPolys):
				mu16CollisionTag_part1 = struct.unpack(">H", f.read(0x2))[0]
				mu16CollisionTag_part0 = struct.unpack(">H", f.read(0x2))[0]
				mau8VertexIndices = struct.unpack(">3B", f.read(0x3))
				terminator = struct.unpack(">b", f.read(0x1))[0]
				mau8EdgeCosines = struct.unpack(">4B", f.read(0x4))
				PolygonSoupPolygons.append([[mu16CollisionTag_part0, mu16CollisionTag_part1], mau8VertexIndices, mau8EdgeCosines])
			
			PolygonSoups.append([maiVertexOffsets, mfComprGranularity, PolygonSoupVertices, PolygonSoupPolygons])
			
	return PolygonSoups


def read_graphicsstub(graphicsstub_path): #ok
	mGraphicsSpecId = mWheelGraphicsSpecId = ""
	with open(graphicsstub_path, "rb") as f:
		mpVehicleGraphics_index, mpWheelGraphics_index = struct.unpack("<ii", f.read(0x8))
		padding = f.read(8)
		
		_ = struct.unpack(">i", f.read(0x4))[0]
		mResourceId = bytes_to_id(f.read(0x4))
		muOffset = struct.unpack(">I", f.read(0x4))[0]
		padding = struct.unpack(">i", f.read(0x4))[0]
		if mpVehicleGraphics_index == 1:
			mGraphicsSpecId = mResourceId
		else:
			mWheelGraphicsSpecId = mResourceId
		
		_ = struct.unpack(">i", f.read(0x4))[0]
		mResourceId = bytes_to_id(f.read(0x4))
		muOffset = struct.unpack(">I", f.read(0x4))[0]
		padding = struct.unpack(">i", f.read(0x4))[0]
		if mpVehicleGraphics_index == 2:
			mGraphicsSpecId = mResourceId
		else:
			mWheelGraphicsSpecId = mResourceId
	
	return ([mGraphicsSpecId, mpVehicleGraphics_index], [mWheelGraphicsSpecId, mpWheelGraphics_index])


def read_graphicsspec(graphicsspec_path): #ok
	muVersion = 0
	instances = []
	with open(graphicsspec_path, "rb") as f:
		muVersion = struct.unpack(">I", f.read(0x4))[0]
		muPartsCount, mppPartModels = struct.unpack(">Ii", f.read(0x8))
		muShatteredGlassPartsCount, mpShatteredGlassParts = struct.unpack(">Ii", f.read(0x8))
		mpPartLocators = struct.unpack(">i", f.read(0x4))[0]
		mpPartVolumeIDs = struct.unpack(">i", f.read(0x4))[0]
		mpNumRigidBodiesForPart = struct.unpack(">i", f.read(0x4))[0]
		mppRigidBodyToSkinMatrixTransforms = struct.unpack(">i", f.read(0x4))[0]
		
		f.seek(mppPartModels, 0)
		model_indices = struct.unpack("<%dI" % muPartsCount, f.read(0x4*muPartsCount))
		
		f.seek(mpShatteredGlassParts, 0)
		shattered_glass = []
		for i in range(0, muShatteredGlassPartsCount):
			mpModel, muBodyPartIndex, muBodyPartType = struct.unpack(">iII", f.read(0xC))
			shattered_glass.append([mpModel, muBodyPartIndex, get_part_type(muBodyPartType)])
		
		mTransforms = []
		for i in range(0, muPartsCount):
			f.seek(mpPartLocators + 0x40*i, 0)
			mTransform = [[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))]]
			mTransform = Matrix(mTransform)
			mTransform = mTransform.transposed()
			mTransforms.append(mTransform)
		
		f.seek(mpPartVolumeIDs, 0)
		part_volume_ids = struct.unpack(">%dB" % muPartsCount, f.read(0x1*muPartsCount))
		
		f.seek(mpNumRigidBodiesForPart, 0)
		rigid_bodies_for_part = struct.unpack(">%dB" % muPartsCount, f.read(0x1*muPartsCount))
		
		f.seek(mppRigidBodyToSkinMatrixTransforms, 0)
		transforms_rigid_body_pointers = []
		for i in range(0, muPartsCount):
			f.seek(mppRigidBodyToSkinMatrixTransforms + 0x4*i, 0)
			transforms_rigid_body_pointers.append(struct.unpack(">i", f.read(0x4))[0])
		
		transforms_rigid_body = []
		for i in range(0, muPartsCount):
			f.seek(transforms_rigid_body_pointers[i], 0)
			mTransform_rigid_body = [[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))],[*struct.unpack(">4f", f.read(0x10))]]
			mTransform_rigid_body = Matrix(mTransform_rigid_body)
			mTransform_rigid_body = mTransform_rigid_body.transposed()
			transforms_rigid_body.append(mTransform_rigid_body)
		
		f.seek(max(transforms_rigid_body_pointers) + 0x40, 0)
		for i in range(0, muPartsCount):
			_ = struct.unpack(">i", f.read(0x4))[0]
			mResourceId = bytes_to_id(f.read(0x4))
			muOffset = struct.unpack(">I", f.read(0x4))[0]
			padding = struct.unpack(">i", f.read(0x4))[0]
			
			is_shattered_glass = False
			instances.append([mResourceId, [mTransforms[i], part_volume_ids[i]], is_shattered_glass])
		
		for i in range(0, muShatteredGlassPartsCount):
			_ = struct.unpack(">i", f.read(0x4))[0]
			mResourceId = bytes_to_id(f.read(0x4))
			muOffset = struct.unpack(">I", f.read(0x4))[0]
			padding = struct.unpack(">i", f.read(0x4))[0]
			
			is_shattered_glass = True
			instances.append([mResourceId, [shattered_glass[i]], is_shattered_glass])
	
	return (muVersion, instances)


def read_wheelgraphicsspec(wheelgraphicsspec_path): #ok
	muVersion = 0
	instances = []
	mTransform = Matrix([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]).transposed()
	
	with open(wheelgraphicsspec_path, "rb") as f:
		muVersion = struct.unpack(">I", f.read(0x4))[0]
		mpWheelModel, mpCaliperModel = struct.unpack(">ii", f.read(0x8))
		padding = f.read(4)
		
		_ = struct.unpack(">i", f.read(0x4))[0]
		mResourceId = bytes_to_id(f.read(0x4))
		muOffset = struct.unpack(">I", f.read(0x4))[0]
		padding = struct.unpack(">i", f.read(0x4))[0]
		is_caliper = False
		
		instances.append([mResourceId, [mTransform], is_caliper])
		
		if mpCaliperModel != -1:
			_ = struct.unpack(">i", f.read(0x4))[0]
			mResourceId = bytes_to_id(f.read(0x4))
			muOffset = struct.unpack(">I", f.read(0x4))[0]
			padding = struct.unpack(">i", f.read(0x4))[0]
			is_caliper = True
			
			instances.append([mResourceId, [mTransform], is_caliper])
		
	return(muVersion, instances)


def read_model(model_path): #ok
	renderables = []
	model_properties = []
	with open(model_path, "rb") as f:
		mppRenderables = struct.unpack(">i", f.read(0x4))[0]
		mpu8StateRenderableIndices = struct.unpack(">i", f.read(0x4))[0]
		mpfLodDistances = struct.unpack(">i", f.read(0x4))[0]
		miGameExplorerIndex = struct.unpack(">i", f.read(0x4))[0]
		mu8NumRenderables = struct.unpack(">B", f.read(0x1))[0]
		mu8Flags = struct.unpack(">B", f.read(0x1))[0]
		mu8NumStates = struct.unpack(">B", f.read(0x1))[0]
		mu8VersionNumber = struct.unpack(">B", f.read(0x1))[0]
		
		f.seek(mppRenderables, 0)
		_ = struct.unpack(">%dI" % mu8NumRenderables, f.read(0x4*mu8NumRenderables))
		
		f.seek(mpu8StateRenderableIndices, 0)
		renderable_indices = struct.unpack(">%dB" % mu8NumRenderables, f.read(0x1*mu8NumRenderables))
		
		f.seek(mpfLodDistances, 0)
		lod_distances = struct.unpack(">%df" % mu8NumRenderables, f.read(0x4*mu8NumRenderables))
		
		padding = calculate_padding(mpfLodDistances + 0x4*mu8NumRenderables, 0x10)
		f.seek(padding, 1)
		
		for i in range(0, mu8NumRenderables):
			_ = struct.unpack(">i", f.read(0x4))[0]
			mResourceId = bytes_to_id(f.read(0x4))
			muOffset = struct.unpack(">I", f.read(0x4))[0]
			padding = struct.unpack(">i", f.read(0x4))[0]
			
			renderables.append([mResourceId, [renderable_indices[i], lod_distances[i]]])
	
		model_properties = [mppRenderables, mpu8StateRenderableIndices, mpfLodDistances, miGameExplorerIndex, mu8NumRenderables, mu8Flags, mu8NumStates, mu8VersionNumber]
	
	return (model_properties, renderables)


def read_renderable(renderable_path): #ok, updated
	meshes = []
	renderable_properties = []
	with open(renderable_path, "rb") as f:
		object_center = struct.unpack(">fff", f.read(0xC))
		object_radius = struct.unpack(">f", f.read(0x4))[0]
		mu16VersionNumber = struct.unpack(">H", f.read(0x2))[0]
		num_meshes = struct.unpack(">H", f.read(0x2))[0]
		meshes_table_pointer = struct.unpack(">i", f.read(0x4))[0]
		_ = struct.unpack(">i", f.read(0x4))[0]
		flags = struct.unpack(">H", f.read(0x2))[0]
		padding = f.read(0x2)
        
		f.seek(meshes_table_pointer, 0)
		meshes_data_pointer = struct.unpack(">%di" % num_meshes, f.read(0x4*num_meshes))
		
		renderable_properties = [object_center, object_radius, mu16VersionNumber, num_meshes, flags]
		
        # read meshes data
		num_vertex_descriptors_total = 0
		for i in range(0, num_meshes):
			f.seek(meshes_data_pointer[i], 0)
			f.seek(0x10, 1)
			
			_ = struct.unpack(">i", f.read(0x4))[0]	#null
			indices_buffer_size0 = struct.unpack(">i", f.read(0x4))[0]
			mesh_unk1 = struct.unpack("<i", f.read(0x4))[0]	#always 0x6
			_ = struct.unpack(">i", f.read(0x4))[0]	#null
			num_vertex_descriptors = struct.unpack(">B", f.read(0x1))[0]
			mesh_unk2 = struct.unpack(">B", f.read(0x1))[0]	#null
			mesh_unk3 = struct.unpack(">B", f.read(0x1))[0]	#always 1
			sub_part_code = struct.unpack(">B", f.read(0x1))[0]
			f.seek(0x1C, 1)
			indices_data_offset = struct.unpack(">i", f.read(0x4))[0]
			_ = struct.unpack(">i", f.read(0x4))[0]	#null
			indices_buffer_size1 = struct.unpack(">i", f.read(0x4))[0]
			mesh_unk4 = struct.unpack(">i", f.read(0x4))[0]	#always 2
			mesh_unk5 = struct.unpack("<i", f.read(0x4))[0]	#always 1
			vertex_data_offset = struct.unpack(">i", f.read(0x4))[0]
			_ = struct.unpack(">i", f.read(0x4))[0]	#null
			vertex_data_size = struct.unpack(">i", f.read(0x4))[0]
			
			if indices_buffer_size0 != indices_buffer_size1:
				print("Warning: the two indices buffer sizes are different in the file %s. Please verify which one is the correct." % renderable_path)
			
			mesh_properties = [[], mesh_unk1, indices_data_offset, indices_buffer_size1, vertex_data_offset, vertex_data_size, num_vertex_descriptors, mesh_unk2, mesh_unk3, sub_part_code]
			meshes.append([i, mesh_properties])
			
			num_vertex_descriptors_total += num_vertex_descriptors
		
		num_resources = num_meshes + num_vertex_descriptors_total
		resource_table_size = num_resources*0x10
		f.seek(-resource_table_size, 2)
		
		for i in range(0, num_meshes):
			_ = struct.unpack(">i", f.read(0x4))[0]
			mMaterialId = bytes_to_id(f.read(0x4))
			muOffset = struct.unpack(">I", f.read(0x4))[0]
			padding = struct.unpack(">i", f.read(0x4))[0]
			
			mVertexDescriptorsId = []
			for j in range(0, meshes[i][1][6]):
				_ = struct.unpack(">i", f.read(0x4))[0]
				mVertexDescriptorsId.append(bytes_to_id(f.read(0x4)))
				muOffset = struct.unpack(">I", f.read(0x4))[0]
				padding = struct.unpack(">i", f.read(0x4))[0]
			
			meshes[i].extend([mMaterialId, mVertexDescriptorsId])
	
	return (renderable_properties, meshes)


def read_vertex_descriptor(vertex_descriptor_path): #ok, updated
	vertex_properties = []
	with open(vertex_descriptor_path, "rb") as f:
		unk1 = struct.unpack(">i", f.read(0x4))[0]
		attibutes_flags = struct.unpack(">i", f.read(0x4))[0]
		unk2 = struct.unpack(">H", f.read(0x2))[0]
		num_vertex_attibutes = struct.unpack(">H", f.read(0x2))[0]
		unk2 = struct.unpack(">H", f.read(0x2))[0]
		_ = struct.unpack(">H", f.read(0x2))[0]
		
		semantic_properties = []
		for i in range(0, num_vertex_attibutes):
			data_type0 = struct.unpack(">B", f.read(0x1))[0]	#data type
			data_type1 = struct.unpack(">B", f.read(0x1))[0]	#count
			data_offset = struct.unpack(">H", f.read(0x2))[0]
			vertex_size = struct.unpack(">H", f.read(0x2))[0]
			semantic_type = struct.unpack(">B", f.read(0x1))[0]
			unk_0x7 = struct.unpack(">B", f.read(0x1))[0]
			
			semantic_type = get_vertex_semantic(semantic_type)
			if semantic_type == "":
				print("WARNING: unknown semantic type on vertex descriptor %s." %vertex_descriptor_path)
			data_type = get_vertex_data_type(data_type0, data_type1)
			
			semantic_properties.append([semantic_type, data_type, data_offset])
		
		vertex_properties = [vertex_size, [semantic_properties]]
		
	return vertex_properties


def read_material(material_path, material_technique_dir, shared_material_technique_dir, material_technique_old_dir): #ok, updated
	material_properties = []
	mShaderId = ""
	material_states = []
	texture_states = []
	with open(material_path, "rb") as f:
		unk_0x0_pointer = struct.unpack(">i", f.read(0x4))[0]
		mResourceId = bytes_to_id(f.read(0x4))
		num_material_states = struct.unpack(">B", f.read(0x1))[0]
		num_texture_states = struct.unpack(">B", f.read(0x1))[0]
		unk_0xA = struct.unpack(">B", f.read(0x1))[0]
		_ = struct.unpack(">B", f.read(0x1))[0]	# null
		unk_0xC_pointer = struct.unpack(">i", f.read(0x4))[0]  #OK
		mpVertexShaderConstants = struct.unpack(">i", f.read(0x4))[0] #OK		# unk_0x14_pointer
		mpPixelShaderConstants = struct.unpack(">i", f.read(0x4))[0] #OK		# unk_0x18_pointer
		unk_0x1C_pointer = struct.unpack(">i", f.read(0x4))[0]	#usually null, except with animation
		
		f.seek(unk_0x0_pointer, 0)
		for i in range(0, num_material_states):
			_ = struct.unpack(">i", f.read(0x4))[0]	#pointer
		
		f.seek(unk_0xC_pointer, 0) #OK
		unk_0x0_pointer_relative2 = []
		maiChannels = []													# texture_sampler_codes
		for i in range(0, num_texture_states):	#0x14 | num_texture_states or unk_0xA
			unk_0x0_pointer_relative2.append(struct.unpack(">i", f.read(0x4))[0])
			unk_0x4_relative2 = f.read(0x4)			#maybe important
			maiChannels.append(struct.unpack(">H", f.read(0x2))[0])
			_ = struct.unpack(">H", f.read(0x2))[0]	#null
			_ = struct.unpack(">i", f.read(0x4))[0]	#null
			unk_0x10_relative2 = f.read(0x4)		#maybe important
		
		for i in range(0, num_texture_states):	#nones # OK
			f.seek(unk_0x0_pointer_relative2[i], 0)
			unk_0x0 = f.read(0x4)
        
		
		# VertexShaderConstants
		f.seek(mpVertexShaderConstants, 0) #OK
		muNumVertexShaderConstantsInstances = struct.unpack(">i", f.read(0x4))[0]			# num_parameters_1
		mpauVertexShaderConstantsInstanceSize = struct.unpack(">i", f.read(0x4))[0]			# pointer_to_01s_1
		mppaVertexShaderConstantsInstanceData = struct.unpack(">i", f.read(0x4))[0]			# pointer_to_parameters_pointers_1
		mpauVertexShaderNamesHash = struct.unpack(">i", f.read(0x4))[0]						# pointer_to_unks_1
		mpaVertexShaderProgramStateHandles = struct.unpack(">i", f.read(0x4))[0]			# pointer_to_unks2_1
		f.seek(mpauVertexShaderConstantsInstanceSize, 0)
		mauVertexShaderConstantsInstanceSize = struct.unpack("<%di" % muNumVertexShaderConstantsInstances, f.read(0x4*muNumVertexShaderConstantsInstances))		# _01s_1
		f.seek(mppaVertexShaderConstantsInstanceData, 0)
		mpafVertexShaderConstantsInstanceData = struct.unpack(">%di" % muNumVertexShaderConstantsInstances, f.read(0x4*muNumVertexShaderConstantsInstances))	# pointer_to_parameters_1
		
		mafVertexShaderConstantsInstanceData = []											# parameters_1
		for i in range(0, muNumVertexShaderConstantsInstances):
			f.seek(mpafVertexShaderConstantsInstanceData[i], 0)
			mafVertexShaderConstantsInstanceData.append(struct.unpack(">ffff", f.read(0x4*4)))
		
		f.seek(mpauVertexShaderNamesHash, 0)
		mauVertexShaderNamesHash = struct.unpack(">%di" % muNumVertexShaderConstantsInstances, f.read(0x4*muNumVertexShaderConstantsInstances))				# unks_1
		
		f.seek(mpaVertexShaderProgramStateHandles, 0)
		#maVertexShaderProgramStateHandles = struct.unpack(">%di" % muNumVertexShaderConstantsInstances, f.read(0x4*muNumVertexShaderConstantsInstances))	# unks2_1
		maVertexShaderProgramStateHandles = []
		for i in range(0, muNumVertexShaderConstantsInstances):
			_ = struct.unpack(">i", f.read(0x4))[0]	
			maVertexShaderProgramStateHandles.append(struct.unpack(">i", f.read(0x4))[0])
		
		# PixelShaderConstants
		f.seek(mpPixelShaderConstants, 0) #OK
		muNumPixelShaderConstantsInstances = struct.unpack(">i", f.read(0x4))[0]			# num_parameters_2
		mpauPixelShaderConstantsInstanceSize = struct.unpack(">i", f.read(0x4))[0]			# pointer_to_01s_2
		mppaPixelShaderConstantsInstanceData = struct.unpack(">i", f.read(0x4))[0]			# pointer_to_parameters_pointers_2
		mpauPixelShaderNamesHash = struct.unpack(">i", f.read(0x4))[0]						# pointer_to_unks_2
		mpaPixelShaderProgramStateHandles = struct.unpack(">i", f.read(0x4))[0]				# pointer_to_unks2_2
		f.seek(mpauPixelShaderConstantsInstanceSize, 0)
		mauPixelShaderConstantsInstanceSize = struct.unpack("<%di" % muNumPixelShaderConstantsInstances, f.read(0x4*muNumPixelShaderConstantsInstances))	# _01s_2
		f.seek(mppaPixelShaderConstantsInstanceData, 0)
		mpafPixelShaderConstantsInstanceData = struct.unpack(">%di" % muNumPixelShaderConstantsInstances, f.read(0x4*muNumPixelShaderConstantsInstances))	# pointer_to_parameters_2
		
		mafPixelShaderConstantsInstanceData = []											# parameters_2
		for i in range(0, muNumPixelShaderConstantsInstances):
			f.seek(mpafPixelShaderConstantsInstanceData[i], 0)
			mafPixelShaderConstantsInstanceData.append(struct.unpack(">ffff", f.read(0x4*4)))
        
		f.seek(mpauPixelShaderNamesHash, 0)
		mauPixelShaderNamesHash = struct.unpack(">%di" % muNumPixelShaderConstantsInstances, f.read(0x4*muNumPixelShaderConstantsInstances))			# unks_2
		
		f.seek(mpaPixelShaderProgramStateHandles, 0)
		#maPixelShaderProgramStateHandles = struct.unpack(">%di" % muNumPixelShaderConstantsInstances, f.read(0x4*muNumPixelShaderConstantsInstances))	# unks2_2
		maPixelShaderProgramStateHandles = []
		for i in range(0, muNumPixelShaderConstantsInstances):
			_ = struct.unpack(">i", f.read(0x4))[0]	
			maPixelShaderProgramStateHandles.append(struct.unpack(">i", f.read(0x4))[0])
        
		
		# Animation
		parameters_3 = []
		anim_strings_3 = []
		if unk_0x1C_pointer != 0x0:
			f.seek(unk_0x1C_pointer, 0)
			_ = struct.unpack(">i", f.read(0x4))[0]	#null
			num_parameters_3 = struct.unpack(">i", f.read(0x4))[0]
			pointer_to_parameters_pointers_3 = struct.unpack(">i", f.read(0x4))[0]
			pointer_to_anim_strings_pointers_3 = struct.unpack(">i", f.read(0x4))[0]
			f.seek(pointer_to_parameters_pointers_3, 0)
			pointer_to_parameters_3 = struct.unpack(">%di" % num_parameters_3, f.read(0x4*num_parameters_3))
			
			for i in range(0, num_parameters_3):
				f.seek(pointer_to_parameters_3[i], 0)
				parameters_3.append(struct.unpack(">ffff", f.read(0x4*4)))
			
			f.seek(pointer_to_anim_strings_pointers_3, 0)
			pointer_to_anim_strings_3 = struct.unpack(">%di" % num_parameters_3, f.read(0x4*num_parameters_3))
			
			for i in range(0, num_parameters_3):
				f.seek(pointer_to_anim_strings_3[i], 0)
				string = b''
				byte = f.read(0x1)
				while byte != b'\x00':
					string += byte[0:1]
					byte = f.read(0x1)
				string = str(string,'ascii')
				anim_strings_3.append(string)
		
		# Padding
		padding = calculate_padding(f.tell(), 0x10)
		f.seek(padding, 1)
        
		# Resources
		#_ = struct.unpack(">i", f.read(0x4))[0]
		#mShaderId = bytes_to_id(f.read(0x4))
		#muOffset = struct.unpack(">I", f.read(0x4))[0]
		#padding = struct.unpack(">i", f.read(0x4))[0]
        
		for i in range(0, num_material_states):
			_ = struct.unpack(">i", f.read(0x4))[0]
			#mMaterialStateId = bytes_to_id(f.read(0x4))
			mMaterialTechniqueId = bytes_to_id(f.read(0x4))
			muOffset = struct.unpack(">I", f.read(0x4))[0]
			padding = struct.unpack(">i", f.read(0x4))[0]
			
			material_technique_path = os.path.join(material_technique_dir, mMaterialTechniqueId + ".dat")
			if not os.path.isfile(material_technique_path):
				material_technique_path = os.path.join(shared_material_technique_dir, mMaterialTechniqueId + ".dat")
				is_shared_asset = True
				if not os.path.isfile(material_technique_path):
					material_technique_path = os.path.join(material_technique_old_dir, mMaterialTechniqueId + ".dat")
					is_shared_asset = False
					if not os.path.isfile(material_technique_path):
						print("WARNING: failed to open material technique %s: no such file in '%s', '%s' and '%s'." % (mMaterialTechniqueId, material_technique_dir, shared_material_technique_dir, material_technique_old_dir))
						continue
			
			with open(material_technique_path, "rb") as g:
				if i == 0:
					g.seek(-0x1C, 2)
					mShaderId = bytes_to_id(g.read(0x4))
				g.seek(-0xC, 2)
				mMaterialStateId = bytes_to_id(g.read(0x4))
			
			material_states.append([mMaterialStateId])
        
		for i in range(0, num_texture_states):
			_ = struct.unpack(">i", f.read(0x4))[0]
			mTextureStateId = bytes_to_id(f.read(0x4))
			muOffset = struct.unpack(">I", f.read(0x4))[0]
			padding = struct.unpack(">i", f.read(0x4))[0]
			
			texture_states.append([mTextureStateId, maiChannels[i]])
		
		material_properties.append([[], [mafVertexShaderConstantsInstanceData, mauVertexShaderNamesHash], [mafPixelShaderConstantsInstanceData, mauPixelShaderNamesHash], [parameters_3, anim_strings_3]])
		
	return (material_properties, mShaderId, material_states, texture_states)


def read_shader(shader_path): #ok
	ShaderType = ""
	raster_types = []
	with open(shader_path, "rb") as f:
		file_size = os.path.getsize(shader_path)
		f.seek(0x94, 0)
		shader_description_offset = struct.unpack(">i", f.read(0x4))[0]	#mpacName
		f.seek(shader_description_offset, 0)
		shader_description = f.read(file_size-shader_description_offset).split(b'\x00')[0]
		shader_description = str(shader_description, 'ascii')
		
		f.seek(0x8, 0)
		muNumVertexShaderConstantsInstances = struct.unpack(">I", f.read(0x4))[0]	#num_parameters_1
		f.seek(0x3C, 0)
		muNumPixelShaderConstantsInstances = struct.unpack(">I", f.read(0x4))[0]	#num_parameters_2
		
		f.seek(0x8C, 0)
		mpaSamplers = struct.unpack(">I", f.read(0x4))[0]	#raster_types_offset
		miNumSamplers = struct.unpack(">b", f.read(0x1))[0]	#num_rasters
		end_raster_types_offset = shader_description_offset
		
		raster_type_offsets = []
		miChannel = []	#raster_indices
		for i in range(0, miNumSamplers):
			f.seek(mpaSamplers + i*0x8, 0)
			raster_type_offsets.append(struct.unpack(">i", f.read(0x4))[0])
			miChannel.append(struct.unpack(">h", f.read(0x2))[0])
		
		raster_type_offsets.append(end_raster_types_offset)
		for i in range(0, miNumSamplers):
			f.seek(raster_type_offsets[i], 0)
			if raster_type_offsets[i] > raster_type_offsets[i+1]:
				raster_type = f.read(end_raster_types_offset-raster_type_offsets[i]).split(b'\x00')[0]
			else:
				raster_type = f.read(raster_type_offsets[i+1]-raster_type_offsets[i]).split(b'\x00')[0]
			raster_type = str(raster_type, 'ascii')
			
			#if miChannel[i] == 15:
			#	continue
			#elif miChannel[i] == 13:
			#	continue
			raster_types.append([miChannel[i], raster_type])
		
		if shader_description == "Vehicle_1Bit_Tyre_Textured_Blurred" or shader_description == "Vehicle_GreyScale_WheelChrome_Textured_Damaged_Blurred":
			#This shader is missing the definition of two map types
			raster_types.append([0, "DiffuseTextureSampler"])
			raster_types.append([2, "NormalTextureSampler"])
		
		
		#if shader_description == "Road_Night_Detailmap_Opaque_Singlesided":
		#	#This shader is missing the definition of two AoMaps
		#	raster_types.append([3, "AoMapSampler"])
		#	raster_types.append([4, "AoMapSampler2"])
		
		#elif shader_description == "Tunnel_Road_Detailmap_Opaque_Singlesided":
		#	#This shader is missing the definition of two AoMaps
		#	raster_types.append([3, "AoMapSampler"])
		#	raster_types.append([4, "AoMapSampler2"])
		
		#elif shader_description == "Cable_GreyScale_Doublesided":
		#	# This shader is used by a material (3A_47_5B_86) that has a different number of parameters 1
		#	# than the specified by the shader
		#	muNumVertexShaderConstantsInstances = 2
		
		##elif shader_description == "Vehicle_Greyscale_Window_Textured":
		##	#This shader has one extra map definition
		##	raster_types.remove([14, "GlassFractureSampler"])
		
		raster_types.sort(key=lambda x:x[0])
		
		raster_types_dict = {}
		for raster_type_data in raster_types:
			raster_types_dict[raster_type_data[0]] = raster_type_data[1]
		
	return (shader_description, raster_types_dict, muNumVertexShaderConstantsInstances, muNumPixelShaderConstantsInstances)


def read_textureState(texture_state_path): #ok, updated
	rasters = []
	texture_state_properties = []
	with open(texture_state_path, "rb") as f:
		#mipmap_lod_bias = struct.unpack(">f", f.read(0x4))[0]
		
		mipmap_lod_bias = 0.0
		addressing_mode = [0, 0, 0]
		filter_types = [0, 0, 0]
		min_max_lod = [0, 0]
		max_anisotropy = 0
		comparison_function = 0
		is_border_color_white = False
		unk1 = 0
		
		f.seek(-0x10, 2)
		_ = struct.unpack(">i", f.read(0x4))[0]
		mRasterId = bytes_to_id(f.read(0x4))
		muOffset = struct.unpack(">I", f.read(0x4))[0]
		padding = struct.unpack(">i", f.read(0x4))[0]
			
		rasters.append([mRasterId])
	
		texture_state_properties = [addressing_mode, filter_types, min_max_lod, max_anisotropy, mipmap_lod_bias,
									comparison_function, is_border_color_white, unk1]
	
	return (texture_state_properties, rasters)


def read_raster(raster_path): #ok, updated
	raster_properties = []
	if os.path.splitext(raster_path)[1] == ".dds":
		return raster_properties
	
	with open(raster_path, "rb") as f:
		#format, width, height, depth, dimension, main_mipmap, mipmap, unk_0x34, unk_0x38
		
		format = struct.unpack(">B", f.read(0x1))[0]
		mipmap = struct.unpack(">B", f.read(0x1))[0]
		dimension = struct.unpack(">B", f.read(0x1))[0]
		cubemap = struct.unpack(">B", f.read(0x1))[0]
		
		remap = struct.unpack(">I", f.read(0x4))[0]
		width = struct.unpack(">H", f.read(0x2))[0]
		height = struct.unpack(">H", f.read(0x2))[0]
		depth = struct.unpack(">H", f.read(0x2))[0]
		
		location = struct.unpack(">B", f.read(0x1))[0]
		padding = struct.unpack(">B", f.read(0x1))[0]
		
		pitch = struct.unpack(">I", f.read(0x4))[0]
		offset = struct.unpack(">I", f.read(0x4))[0]
		buffer = struct.unpack(">I", f.read(0x4))[0]
		storeType = struct.unpack(">I", f.read(0x4))[0]
		storeFlags = struct.unpack(">I", f.read(0x4))[0]
		
		format = get_fourcc(format)
		
		if dimension == 1:	 # 1D
			dimension = 0
		elif dimension == 2: # 2D
			dimension = 1
		elif dimension == 3: # 3D
			dimension = 2
		
		raster_properties = [format, width, height, depth, dimension, mipmap]
	
	return raster_properties


def read_deformationspec(deformationspec_path): #ok
	maWheelSpecs = []
	maDeformationSensorSpecs = []
	mCarModelSpaceToHandlingBodySpaceTransform = []
	TagPointSpecs = []
	DrivenPoints = []
	GenericTags = []
	CameraTags = []
	LightTags = []
	IKPartData = []
	GlassPaneData = []
	with open(deformationspec_path, "rb") as f:
		miVersionNumber = struct.unpack(">i", f.read(0x4))[0]
		maTagPointData = struct.unpack(">i", f.read(0x4))[0]
		miNumberOfTagPoints = struct.unpack(">i", f.read(0x4))[0]
		maDrivenPointData = struct.unpack(">i", f.read(0x4))[0]
		miNumberOfDrivenPoints = struct.unpack(">i", f.read(0x4))[0]
		
		maIKPartData = struct.unpack(">i", f.read(0x4))[0]
		miNumberOfIKParts = struct.unpack(">i", f.read(0x4))[0]
		maGlassPaneData = struct.unpack(">i", f.read(0x4))[0]
		miNumGlassPanes = struct.unpack(">i", f.read(0x4))[0]
		mGenericTags = struct.unpack(">Ii", f.read(0x8))
		mCameraTags = struct.unpack(">Ii", f.read(0x8))
		mLightTags = struct.unpack(">Ii", f.read(0x8))
		padding = f.read(0x4)
		
		mHandlingBodyDimensions = struct.unpack(">4f", f.read(0x10))
		
		maWheelSpecs.append([[*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], struct.unpack(">i", f.read(0x4))[0], "FR"])
		padding = f.read(0xC)
		maWheelSpecs.append([[*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], struct.unpack(">i", f.read(0x4))[0], "FL"])
		padding = f.read(0xC)
		maWheelSpecs.append([[*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], struct.unpack(">i", f.read(0x4))[0], "RR"])
		padding = f.read(0xC)
		maWheelSpecs.append([[*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], struct.unpack(">i", f.read(0x4))[0], "RL"])
		padding = f.read(0xC)
		
		if maTagPointData == 0x930:
			# BETA
			for i in range(0, 20):
				maDirectionParams = []
				_ = f.read(0x10)
				_ = f.read(0x10)
				_ = f.read(0x10)
				mfRadius = struct.unpack(">f", f.read(0x4))[0]
				_ = f.read(0xC)
				mInitialOffset = struct.unpack(">3f", f.read(0xC))
				_ = f.read(0x4)
				maNextSensor = struct.unpack(">6B", f.read(0x6))
				mu8SceneIndex = struct.unpack(">B", f.read(0x1))[0]
				mu8AbsorbtionLevel = struct.unpack(">B", f.read(0x1))[0]
				mau8NextBoundarySensor = struct.unpack(">2B", f.read(0x2))
				padding = f.read(0x6)
				maDeformationSensorSpecs.append([mInitialOffset, maDirectionParams, mfRadius, maNextSensor, mu8SceneIndex, mu8AbsorbtionLevel, mau8NextBoundarySensor])
		else:
			for i in range(0, 20):
				mInitialOffset = struct.unpack(">3f", f.read(0xC))
				_ = f.read(0x4)
				maDirectionParams = struct.unpack(">6f", f.read(0x18))
				mfRadius = struct.unpack(">f", f.read(0x4))[0]
				maNextSensor = struct.unpack(">6B", f.read(0x6))
				mu8SceneIndex = struct.unpack(">B", f.read(0x1))[0]
				mu8AbsorbtionLevel = struct.unpack(">B", f.read(0x1))[0]
				mau8NextBoundarySensor = struct.unpack(">2B", f.read(0x2))
				padding = f.read(0xA)
				maDeformationSensorSpecs.append([mInitialOffset, maDirectionParams, mfRadius, maNextSensor, mu8SceneIndex, mu8AbsorbtionLevel, mau8NextBoundarySensor])
		
		mCarModelSpaceToHandlingBodySpaceTransform = [[*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))]]
		mCarModelSpaceToHandlingBodySpaceTransform = Matrix(mCarModelSpaceToHandlingBodySpaceTransform)
		mCarModelSpaceToHandlingBodySpaceTransform = mCarModelSpaceToHandlingBodySpaceTransform.transposed()
		
		mu8SpecID = struct.unpack(">B", f.read(0x1))[0]
		mu8NumVehicleBodies = struct.unpack(">B", f.read(0x1))[0]
		mu8NumDeformationSensors = struct.unpack(">B", f.read(0x1))[0]
		mu8NumGraphicsParts = struct.unpack(">B", f.read(0x1))[0]
		padding = f.read(0xC)
		
		mCurrentCOMOffset = struct.unpack(">4f", f.read(0x10))
		mMeshOffset = struct.unpack(">4f", f.read(0x10))
		mRigidBodyOffset = struct.unpack(">4f", f.read(0x10))
		mCollisionOffset = struct.unpack(">4f", f.read(0x10))
		mInertiaTensor = struct.unpack(">4f", f.read(0x10))
		
		#TagPointSpec
		f.seek(maTagPointData, 0)
		for i in range(0, miNumberOfTagPoints):
			mOffsetFromA = struct.unpack(">3f", f.read(0xC))
			mWeightA = struct.unpack(">f", f.read(0x4))[0]
			mOffsetFromB = struct.unpack(">3f", f.read(0xC))
			mWeightB = struct.unpack(">f", f.read(0x4))[0]
			mInitialPosition = struct.unpack(">3f", f.read(0xC))
			mDetachThreshold = struct.unpack(">f", f.read(0x4))[0]
			mfWeightA = struct.unpack(">f", f.read(0x4))[0]					# same as mWeightA
			mfWeightB = struct.unpack(">f", f.read(0x4))[0]					# same as mWeightB
			mfDetachThresholdSquared = struct.unpack(">f", f.read(0x4))[0]	# same as mDetachThreshold
			miDeformationSensorA = struct.unpack(">h", f.read(0x2))[0]
			miDeformationSensorB = struct.unpack(">h", f.read(0x2))[0]
			miJointIndex = struct.unpack(">b", f.read(0x1))[0]
			mbSkinnedPoint = bool(struct.unpack(">B", f.read(0x1))[0])
			padding = f.read(0xE)
			TagPointSpecs.append([mInitialPosition, mfWeightA, mfWeightB, mfDetachThresholdSquared, miDeformationSensorA, miDeformationSensorB, miJointIndex, mbSkinnedPoint])
		
		
		#DrivenPoints
		f.seek(maDrivenPointData, 0)
		for i in range(0, miNumberOfDrivenPoints):
			mInitialPos = struct.unpack(">3f", f.read(0xC))
			_ = f.read(0x4)
			mfDistanceFromA = struct.unpack(">f", f.read(0x4))[0]
			mfDistanceFromB = struct.unpack(">f", f.read(0x4))[0]
			miTagPointIndexA = struct.unpack(">h", f.read(0x2))[0]
			miTagPointIndexB = struct.unpack(">h", f.read(0x2))[0]
			padding = f.read(0x4)
			DrivenPoints.append([mInitialPos, miTagPointIndexA, miTagPointIndexB])
		
		
		#mGenericTags
		f.seek(mGenericTags[1], 0)
		for i in range(0, mGenericTags[0]):
			mLocatorMatrix = [[*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))]]
			mLocatorMatrix = Matrix(mLocatorMatrix)
			mLocatorMatrix = mLocatorMatrix.transposed()
			meTagPointType = struct.unpack(">i", f.read(0x4))[0]
			miIkPartIndex = struct.unpack(">h", f.read(0x2))[0]
			mu8SkinPoint = struct.unpack(">B", f.read(0x1))[0]
			padding = f.read(0x9)
			
			GenericTags.append([i, mLocatorMatrix, get_tag_point_type(meTagPointType), miIkPartIndex, mu8SkinPoint])
		
		#mCameraTags
		f.seek(mCameraTags[1], 0)
		for i in range(0, mCameraTags[0]):
			mLocatorMatrix = [[*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))]]
			mLocatorMatrix = Matrix(mLocatorMatrix)
			mLocatorMatrix = mLocatorMatrix.transposed()
			meTagPointType = struct.unpack(">i", f.read(0x4))[0]
			miIkPartIndex = struct.unpack(">h", f.read(0x2))[0]
			mu8SkinPoint = struct.unpack(">B", f.read(0x1))[0]
			padding = f.read(0x9)
			
			CameraTags.append([i, mLocatorMatrix, get_tag_point_type(meTagPointType), miIkPartIndex, mu8SkinPoint])
		
		#mLightTags
		f.seek(mLightTags[1], 0)
		for i in range(0, mLightTags[0]):
			mLocatorMatrix = [[*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))]]
			mLocatorMatrix = Matrix(mLocatorMatrix)
			mLocatorMatrix = mLocatorMatrix.transposed()
			meTagPointType = struct.unpack(">i", f.read(0x4))[0]
			miIkPartIndex = struct.unpack(">h", f.read(0x2))[0]
			mu8SkinPoint = struct.unpack(">B", f.read(0x1))[0]
			padding = f.read(0x9)
			
			LightTags.append([i, mLocatorMatrix, get_tag_point_type(meTagPointType), miIkPartIndex, mu8SkinPoint])
		
		#maIKPartData
		f.seek(maIKPartData, 0)
		for i in range(0, miNumberOfIKParts):
			f.seek(maIKPartData + 0x1E0*i, 0)
			mGraphicsTransform = [[*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))]]
			mGraphicsTransform = Matrix(mGraphicsTransform)
			mGraphicsTransform = mGraphicsTransform.transposed()
			
			##mBBoxSkinData
			mOrientation = [[*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))], [*struct.unpack(">4f", f.read(0x10))]]
			mOrientation = Matrix(mOrientation)
			mOrientation = mOrientation.transposed()
			
			#maCornerSkinData[8]
			maCornerSkinData = []
			for j in range(0, 8):
				maCornerSkinData_mVertex = struct.unpack(">4f", f.read(0x10))
				maCornerSkinData_mafWeights = struct.unpack(">3f", f.read(0xC))
				maCornerSkinData_mauBoneIndices = struct.unpack(">3B", f.read(0x3))
				_ = struct.unpack(">B", f.read(0x1))[0]
				maCornerSkinData.append([maCornerSkinData_mVertex, maCornerSkinData_mafWeights, maCornerSkinData_mauBoneIndices])
			
			#mCentreSkinData
			mCentreSkinData_mVertex = struct.unpack(">4f", f.read(0x10))
			mCentreSkinData_mafWeights = struct.unpack(">3f", f.read(0xC))
			mCentreSkinData_mauBoneIndices = struct.unpack(">3B", f.read(0x3))
			_ = struct.unpack(">B", f.read(0x1))[0]
			mCentreSkinData = [mCentreSkinData_mVertex, mCentreSkinData_mafWeights, mCentreSkinData_mauBoneIndices]
			
			#mJointSkinData
			mJointSkinData_mVertex = struct.unpack(">4f", f.read(0x10))
			mJointSkinData_mafWeights = struct.unpack(">3f", f.read(0xC))
			mJointSkinData_mauBoneIndices = struct.unpack(">3B", f.read(0x3))
			_ = struct.unpack(">B", f.read(0x1))[0]
			mJointSkinData = [mJointSkinData_mVertex, mJointSkinData_mafWeights, mJointSkinData_mauBoneIndices]
			mBBoxSkinData = [mOrientation, maCornerSkinData, mCentreSkinData, mJointSkinData]
			
			
			mpaJointSpecs = struct.unpack(">i", f.read(0x4))[0]
			miNumJoints = struct.unpack(">i", f.read(0x4))[0]
			miPartGraphics = struct.unpack(">i", f.read(0x4))[0]
			miStartIndexOfDrivenPoints = struct.unpack(">i", f.read(0x4))[0]
			miNumberOfDrivenPoints = struct.unpack(">i", f.read(0x4))[0]
			miStartIndexOfTagPoints = struct.unpack(">i", f.read(0x4))[0]
			miNumberOfTagPoints = struct.unpack(">i", f.read(0x4))[0]
			mePartType = struct.unpack(">i", f.read(0x4))[0]
			
			##mJointSpecs
			mJointSpecs = []
			f.seek(mpaJointSpecs, 0)
			for j in range(0, miNumJoints):
				mJointPosition = struct.unpack(">4f", f.read(0x10))
				mJointAxis = struct.unpack(">4f", f.read(0x10))
				mJointDefaultDirection = struct.unpack(">4f", f.read(0x10))
				mfMaxJointAngle = struct.unpack(">f", f.read(0x4))[0]
				mfJointDetachThreshold = struct.unpack(">f", f.read(0x4))[0]
				meJointType = struct.unpack(">i", f.read(0x4))[0]
				_ = struct.unpack(">i", f.read(0x4))[0]
				mJointSpecs.append([mJointPosition, mJointAxis, mJointDefaultDirection, mfMaxJointAngle, mfJointDetachThreshold, get_joint_type(meJointType)])
			
			IKPartData.append([mGraphicsTransform, mBBoxSkinData, mJointSpecs, miPartGraphics, miStartIndexOfDrivenPoints,
							  miNumberOfDrivenPoints, miStartIndexOfTagPoints, miNumberOfTagPoints, get_part_type(mePartType)])
		
		#mGlassPaneData
		if miNumGlassPanes > 0:
			f.seek(maGlassPaneData, 0)
			for i in range(0, miNumGlassPanes):
				glasspane_0x00 = struct.unpack(">4f", f.read(0x10))
				glasspane_0x10 = [struct.unpack(">4f", f.read(0x10)), struct.unpack(">4f", f.read(0x10)), struct.unpack(">4f", f.read(0x10)), struct.unpack(">4f", f.read(0x10))]
				glasspane_0x50 = struct.unpack(">4h", f.read(0x8))
				glasspane_0x58 = struct.unpack(">4B", f.read(0x4))
				glasspane_0x5C = struct.unpack(">h", f.read(0x2))[0]
				glasspane_0x5E = struct.unpack(">h", f.read(0x2))[0]
				glasspane_0x60 = struct.unpack(">h", f.read(0x2))[0]
				padding = f.read(0x2)
				mePartType = struct.unpack(">i", f.read(0x4))[0]
				padding = f.read(0x8)
				GlassPaneData.append([glasspane_0x00, glasspane_0x10, glasspane_0x50, glasspane_0x58, glasspane_0x5C, glasspane_0x5E, glasspane_0x60, get_part_type(mePartType)])
	
	mNums = [mu8NumVehicleBodies, mu8NumGraphicsParts]
	mOffsetsAndTensor = [mCurrentCOMOffset, mMeshOffset, mRigidBodyOffset, mCollisionOffset, mInertiaTensor]
	return (mCarModelSpaceToHandlingBodySpaceTransform, mHandlingBodyDimensions, maWheelSpecs, maDeformationSensorSpecs, mu8SpecID, mNums, mOffsetsAndTensor, TagPointSpecs, DrivenPoints, GenericTags, CameraTags, LightTags, IKPartData, GlassPaneData)


def create_renderable(renderable, vertex_descriptors): #ok, updated
	mRenderableId = renderable[0]
	meshes_info = renderable[1][0]
	renderable_properties = renderable[1][1]
	is_shared_asset = renderable[-2]
	renderable_path = renderable[-1]
	
	num_meshes = renderable_properties[3]
	renderable_body_path = os.path.splitext(renderable_path)[0] + "_model" + os.path.splitext(renderable_path)[1]
	with open(renderable_body_path, "rb") as f:
		indices_buffer = [[] for _ in range(num_meshes)]
		vertices_buffer = [[] for _ in range(num_meshes)]
		
		for mesh_info in meshes_info:
			mesh_index = mesh_info[0]
			mesh_properties = mesh_info[1]
			f.seek(mesh_properties[2], 0)
			
			#reading the first vertex_descriptor
			vertex_size = 0
			semantic_properties = []
			mVertexDescriptorsId_main = mesh_info[-1][0]
			for vertex_descriptor in vertex_descriptors:
				if mVertexDescriptorsId_main == vertex_descriptor[0]:
					vertex_properties = vertex_descriptor[1][0]
					vertex_size = vertex_properties[0]
					semantic_properties = vertex_properties[1][0]
					break
			
			semantic_types = []
			for semantic in semantic_properties:
				semantic_types.append(semantic[0])
			
			mesh_indices = []
			
			tristrip_indices = []
			for i in range(0, mesh_properties[3]):
				index = struct.unpack(">H", f.read(0x2))[0]
				if index != 0xFFFF and index >= mesh_properties[5]/vertex_size:
					continue
				tristrip_indices.append(index)
			
			for index in tristrip_indices:
				if index in mesh_indices:
					continue
				if index == 0xFFFF:
					continue
				mesh_indices.append(index)
			
			indices_buffer[mesh_index] = get_triangle_from_trianglestrip(tristrip_indices, mesh_properties[5]/vertex_size)
			
			mesh_vertices_buffer = []
			
			f.seek(mesh_properties[4], 0)
			for index in mesh_indices:
				position = []
				normal = []
				color = []
				tangent = []
				uv1 = []
				uv2 = []
				uv3 = []
				blend_indices = []
				blend_weight = []
				for semantic in semantic_properties:
					f.seek(mesh_properties[4] + index*vertex_size, 0)
					semantic_type = semantic[0]
					data_type = semantic[1]
					data_offset = semantic[2]
					
					#print(hex(f.tell()), "mesh_index", hex(mesh_index), semantic, hex(index), hex(vertex_size))
					#print("mesh_unk1", hex(mesh_properties[1]), "indices_data_offset", hex(mesh_properties[2]), "indices_buffer_size1", hex(mesh_properties[3]), "vertex_data_offset", hex(mesh_properties[4]), "vertex_data_size", hex(mesh_properties[5]), "num_vertex_descriptors", hex(mesh_properties[6]))
					
					f.seek(data_offset, 1)
					
					if data_type[0][-1] == "e":
						values = frombuffer(f.read(data_type[1]), dtype=">%s" % data_type[0][-1])	#np.frombuffer
					elif "packed" in data_type[0]:
						values = f.read(4)
						if semantic_type == "NORMAL":
							string = ''.join(format(byte, '08b') for byte in values)
							sign_b = int(string[0], 2)
							b = int(string[1:10], 2)
							sign_g = int(string[10], 2)
							g = int(string[11:21], 2)
							sign_r = int(string[21], 2)
							r = int(string[22:32], 2)
							
							# Normalization
							if sign_r == 1:
								r = r - 1023.0
							if sign_g == 1:
								g = g - 1023.0
							if sign_b == 1:
								b = b - 511.0
						else:
							string = ''.join(format(byte, '08b') for byte in values)[2:]
							sign_b = int(string[0], 2)
							b = int(string[1:10], 2)
							sign_g = int(string[10], 2)
							g = int(string[11:20], 2)
							sign_r = int(string[20], 2)
							r = int(string[21:30], 2)
							
							# Normalization
							if sign_r == 1:
								r = r - 511.0
							if sign_g == 1:
								g = g - 511.0
							if sign_b == 1:
								b = b - 511.0
						mod = (r*r+g*g+b*b)**0.5
						if mod != 0.0:
							valueR = r/mod
							valueG = g/mod
							valueB = b/mod
						else:
							valueR = 0.0
							valueG = 0.0
							valueB = 0.0
						values = [valueR, valueG, valueB]
					else:
						values = struct.unpack(">%s" % data_type[0], f.read(data_type[1]))
					
					if semantic_type == "POSITION":
						position = values
					elif semantic_type == "POSITIONT":
						pass
					elif semantic_type == "NORMAL":
						normal = values
					elif semantic_type == "COLOR":
						color = values
					elif semantic_type == "TEXCOORD1":
						uv1 = values
					elif semantic_type == "TEXCOORD2":
						uv2 = values
					elif semantic_type == "TEXCOORD3":
						uv3 = values
					elif semantic_type == "TEXCOORD4":
						pass
					elif semantic_type == "TEXCOORD5":
						pass
					elif semantic_type == "TEXCOORD6":
						pass
					elif semantic_type == "TEXCOORD7":
						pass
					elif semantic_type == "TEXCOORD8":
						pass
					elif semantic_type == "BLENDINDICES":
						blend_indices = values
					elif semantic_type == "BLENDWEIGHT":
						blend_weight = values
					elif semantic_type == "TANGENT":
						tangent = values
					elif semantic_type == "BINORMAL":
						pass
					elif semantic_type == "COLOR2":
						pass
					elif semantic_type == "PSIZE":
						pass
				
				mesh_vertices_buffer.append([index, position, normal, tangent, color, uv1, uv2, uv3, blend_indices, blend_weight])
			
			vertices_buffer[mesh_index] = [semantic_types, mesh_vertices_buffer]
	
	
	#==================================================================================================
	#Building Mesh
	#==================================================================================================
	me_ob = bpy.data.meshes.new(mRenderableId)
	obj = bpy.data.objects.new(mRenderableId, me_ob)
	
	#Get a BMesh representation
	bm = bmesh.new()
	
	#Creating new properties
	blend_index1 = (bm.verts.layers.int.get("blend_index1") or bm.verts.layers.int.new('blend_index1'))
	blend_index2 = (bm.verts.layers.int.get("blend_index2") or bm.verts.layers.int.new('blend_index2'))
	blend_index3 = (bm.verts.layers.int.get("blend_index3") or bm.verts.layers.int.new('blend_index3'))
	blend_index4 = (bm.verts.layers.int.get("blend_index4") or bm.verts.layers.int.new('blend_index4'))
	
	blend_weight1 = (bm.verts.layers.float.get("blend_weight1") or bm.verts.layers.float.new('blend_weight1'))
	blend_weight2 = (bm.verts.layers.float.get("blend_weight2") or bm.verts.layers.float.new('blend_weight2'))
	blend_weight3 = (bm.verts.layers.float.get("blend_weight3") or bm.verts.layers.float.new('blend_weight3'))
	blend_weight4 = (bm.verts.layers.float.get("blend_weight4") or bm.verts.layers.float.new('blend_weight4'))
	
	vert_indices = [[] for _ in range(num_meshes)]
	normal_data = []
	has_some_normal_data = False
	
	for mesh_info in meshes_info:
		mesh_index = mesh_info[0]
		mMaterialId = mesh_info[-2]
		indices = indices_buffer[mesh_index]
		semantic_types, mesh_vertices_buffer = vertices_buffer[mesh_index]
		
		#add material to the mesh list of materials
		me_ob.materials.append(bpy.data.materials.get(mMaterialId))
		
		BMVert_dictionary = {}
		
		if "TEXCOORD1" in semantic_types:
			uvName = "UVMap"
			uv_layer = bm.loops.layers.uv.get(uvName) or bm.loops.layers.uv.new(uvName)
		
		if "TEXCOORD2" in semantic_types:
			uvName = "UV2Map"
			uv2_layer = bm.loops.layers.uv.get(uvName) or bm.loops.layers.uv.new(uvName)
		
		if "TEXCOORD3" in semantic_types:
			uvName = "UV3Map"
			uv3_layer = bm.loops.layers.uv.get(uvName) or bm.loops.layers.uv.new(uvName)
		
		for vertex_data in mesh_vertices_buffer:
			index, position, normal, tangent, color, uv1, uv2, uv3, blend_indices, blend_weight = vertex_data
			BMVert = bm.verts.new(position)
			BMVert.index = index
			BMVert_dictionary[index] = [BMVert, uv1, uv2, uv3]
			vert_indices[mesh_index].append(BMVert.index)
			
			if "NORMAL" in semantic_types:
				BMVert.normal = normal
				normal_data.append([index, normal])
				if has_some_normal_data == False:
					me_ob.create_normals_split()
				has_some_normal_data = True
			else:
				normal_data.append([index, (0.0, 0.0, 0.0)])
			
			if "BLENDINDICES" in semantic_types:
				BMVert[blend_index1] = blend_indices[0]
				BMVert[blend_index2] = blend_indices[1]
				BMVert[blend_index3] = blend_indices[2]
				BMVert[blend_index4] = blend_indices[3]
				
			if "BLENDWEIGHT" in semantic_types:
				BMVert[blend_weight1] = blend_weight[0]*100.0/255.0
				BMVert[blend_weight2] = blend_weight[1]*100.0/255.0
				BMVert[blend_weight3] = blend_weight[2]*100.0/255.0
				BMVert[blend_weight4] = blend_weight[3]*100.0/255.0
		
		for i, face in enumerate(indices):
			face_vertices = [BMVert_dictionary[face[0]][0], BMVert_dictionary[face[1]][0], BMVert_dictionary[face[2]][0]]
			BMFace = bm.faces.get(face_vertices) or bm.faces.new(face_vertices)
			if BMFace.index != -1:
				BMFace = BMFace.copy(verts=False, edges=False)
			BMFace.index = i
			BMFace.smooth = True
			#BMFace.material_index = me_ob.materials.find(mMaterialId)	#issue with duplicated materials
			BMFace.material_index = mesh_index
			
			if "TEXCOORD1" in semantic_types:
				for index, loop in enumerate(BMFace.loops):
					loop[uv_layer].uv = [BMVert_dictionary[loop.vert.index][1][0], -BMVert_dictionary[loop.vert.index][1][1]]
			if "TEXCOORD2" in semantic_types:
				for index, loop in enumerate(BMFace.loops):
					loop[uv2_layer].uv = [BMVert_dictionary[loop.vert.index][2][0], -BMVert_dictionary[loop.vert.index][2][1]]
			if "TEXCOORD3" in semantic_types:
				for index, loop in enumerate(BMFace.loops):
					loop[uv3_layer].uv = [BMVert_dictionary[loop.vert.index][3][0], -BMVert_dictionary[loop.vert.index][3][1]]
	
	#Finish up, write the bmesh back to the mesh
	bm.to_mesh(me_ob)
	bm.free()
	
	if has_some_normal_data:
		temp = []
		for data in normal_data:
			temp.append(data[1])
		normal_data = temp[:]
		
		me_ob.validate(clean_customdata=False)
		me_ob.normals_split_custom_set_from_vertices( normal_data )
		me_ob.use_auto_smooth = True
	else:
		me_ob.calc_normals()
	
	#Properties
	#num_vertex_descriptors_s = []
	sub_part_codes = []
	mVertexDescriptorsIds = []
	for mesh_info in meshes_info:
		#mTransform = mesh_info[1][0]
		#mesh_unk1 = mesh_info[1][1]
		#num_vertex_descriptors_s.append(mesh_info[1][6])
		#mesh_unk2 = mesh_info[1][7]
		#mesh_unks3.append(mesh_info[1][8])
		sub_part_codes.append(mesh_info[1][9])
		mVertexDescriptorsIds.append(mesh_info[-1])
	#me_ob["num_vertex_descriptors"] = num_vertex_descriptors_s
	me_ob["sub_part_code"] = sub_part_codes
	me_ob["VertexDescriptorIds"] = mVertexDescriptorsIds
	
	return obj


def create_raster(raster_path, raster_properties): #ok, updated (convert functions removed)
	file, ext = os.path.splitext(raster_path)
	if ext == ".dds":
		return raster_path
	
	raster_body = file + "_texture" + ext
	raster_path = file + ".dds"
	
	with open(raster_path, "wb") as f:
		# remap, pitch, storeFlags
		format, width, height, depth, dimension, mipMapCount = raster_properties
		
		#struct DDS_PIXELFORMAT
		# {
			# uint32  size;
			# uint32  flags;
			# uint32  fourCC;
			# uint32  RGBBitCount;
			# uint32  RBitMask;
			# uint32  GBitMask;
			# uint32  BBitMask;
			# uint32  ABitMask;
		# };
		
		
		# https://docs.microsoft.com/en-us/windows/win32/direct3ddds/dds-header
		# https://docs.microsoft.com/en-us/windows/win32/direct3ddds/dds-pixelformat
		
		DDS_MAGIC = 0x20534444
		header_size = 0x7C
		caps3 = 0
		caps4 = 0
		reserved1 = 0
		reserved2 = 0
		compressed = True
		cubemap = False
		alpha = False
		pitch = True
		
		if "DXT" in format:
			dwFourCC = format
			dwRGBBitCount = 0
			dwRBitMask = 0
			dwGBitMask = 0
			dwBBitMask = 0
			dwABitMask = 0
		else:
			alpha = True
			compressed = False
			dwRGBBitCount = 32
			dwRBitMask = 0xFF0000
			dwGBitMask = 0xFF00
			dwBBitMask = 0xFF
			dwABitMask = 0xFF000000
		
		# block-compressed
		block_size = 16
		if format == "DXT1" or format == "BC1" or format == "BC4":
			block_size = 8
		pitchOrLinearSize = max( 1, int((width+3)/4) ) * block_size
		
		# Flags
		DDSD_CAPS = 0x1
		DDSD_HEIGHT = 0x2
		DDSD_WIDTH = 0x4
		DDSD_PITCH = 0x8
		DDSD_PIXELFORMAT = 0x1000
		DDSD_MIPMAPCOUNT = 0x20000
		DDSD_LINEARSIZE = 0x80000
		DDSD_DEPTH = 0x800000
        
		flags = DDSD_CAPS + DDSD_HEIGHT + DDSD_WIDTH
		flags += DDSD_PIXELFORMAT
		if mipMapCount > 0:
			flags += DDSD_MIPMAPCOUNT
		if compressed == False and pitch:
			flags += DDSD_PITCH
		if compressed and pitch:
			flags += DDSD_LINEARSIZE
		if depth > 1:
			flags += DDSD_DEPTH
		
		# DDS pixel format
		dwSize = 32
		
		DDPF_ALPHAPIXELS = 0x1
		DDPF_ALPHA = 0x2
		DDPF_FOURCC = 0x4
		DDPF_RGB = 0x40
		DDPF_YUV = 0x200
		DDPF_LUMINANCE = 0x20000
		dwFlags = 0
		
		if alpha:
			dwFlags += DDPF_ALPHAPIXELS
		if alpha and compressed: #compressed == False
			dwFlags += DDPF_ALPHA
		if compressed:
			dwFlags += DDPF_FOURCC
		if compressed == False:
			dwFlags += DDPF_RGB
		
		# Caps flags
		DDSCAPS_COMPLEX = 0x8
		DDSCAPS_MIPMAP = 0x400000
		DDSCAPS_TEXTURE = 0x1000
		caps = DDSCAPS_TEXTURE
		if mipMapCount > 0 or depth > 1 or cubemap:
			caps += DDSCAPS_COMPLEX
		if mipMapCount > 0:
			caps += DDSCAPS_MIPMAP
		
		# Caps2 flags
		DDSCAPS2_CUBEMAP = 0x200
		DDSCAPS2_CUBEMAP_POSITIVEX = 0x400
		DDSCAPS2_CUBEMAP_NEGATIVEX = 0x800
		DDSCAPS2_CUBEMAP_POSITIVEY = 0x1000
		DDSCAPS2_CUBEMAP_NEGATIVEY = 0x2000
		DDSCAPS2_CUBEMAP_POSITIVEZ = 0x4000
		DDSCAPS2_CUBEMAP_NEGATIVEZ = 0x8000
		DDSCAPS2_VOLUME = 0x200000
		caps2 = 0x0
		if cubemap:
			caps2 += DDSCAPS2_CUBEMAP
			caps2 += DDSCAPS2_CUBEMAP_POSITIVEX + DDSCAPS2_CUBEMAP_NEGATIVEX
			caps2 += DDSCAPS2_CUBEMAP_POSITIVEY + DDSCAPS2_CUBEMAP_NEGATIVEY
			caps2 += DDSCAPS2_CUBEMAP_POSITIVEZ + DDSCAPS2_CUBEMAP_NEGATIVEZ
		if dimension == 3:
			caps2 += DDSCAPS2_VOLUME
        
		f.write(struct.pack("<I", DDS_MAGIC))			#OK
		f.write(struct.pack("<I", header_size))			#OK
		f.write(struct.pack("<I", flags))
		f.write(struct.pack("<I", height))				#OK
		f.write(struct.pack("<I", width))				#OK
		f.write(struct.pack("<I", pitchOrLinearSize))   #OK
		f.write(struct.pack("<I", depth))	#only if DDS_HEADER_FLAGS_VOLUME is set in flags
		f.write(struct.pack("<I", mipMapCount))			#OK
		f.write(struct.pack("<11I", *[reserved1]*11))   #OK
		
		# DDS_PIXELFORMAT
		f.write(struct.pack("<I", dwSize))
		f.write(struct.pack("<I", dwFlags))
		if compressed:
			f.write(dwFourCC.encode())
		else:
			f.write(struct.pack("<I", 0))
		f.write(struct.pack("<I", dwRGBBitCount))
		f.write(struct.pack("<I", dwRBitMask))
		f.write(struct.pack("<I", dwGBitMask))
		f.write(struct.pack("<I", dwBBitMask))
		f.write(struct.pack("<I", dwABitMask))
		
		f.write(struct.pack("<I", caps))
		f.write(struct.pack("<I", caps2))
		f.write(struct.pack("<I", caps3))               #OK
		f.write(struct.pack("<I", caps4))               #OK
		f.write(struct.pack("<I", reserved2))           #OK
		
		with open(raster_body, "rb") as g:
			f.write(g.read())
		
	return raster_path


def create_polygonsoup(polygonsoup_object_name, PolygonSoupVertices, PolygonSoupPolygons): #ok
	me_ob = bpy.data.meshes.new(polygonsoup_object_name)
	obj = bpy.data.objects.new(polygonsoup_object_name, me_ob)
	
	bm = bmesh.new()
	
	#Creating new properties
	edge_cosine1 = (bm.faces.layers.int.get("edge_cosine1") or bm.faces.layers.int.new('edge_cosine1'))
	edge_cosine2 = (bm.faces.layers.int.get("edge_cosine2") or bm.faces.layers.int.new('edge_cosine2'))
	edge_cosine3 = (bm.faces.layers.int.get("edge_cosine3") or bm.faces.layers.int.new('edge_cosine3'))
	edge_cosine4 = (bm.faces.layers.int.get("edge_cosine4") or bm.faces.layers.int.new('edge_cosine4'))
	collision_tag0 = (bm.faces.layers.int.get("collision_tag0") or bm.faces.layers.int.new('collision_tag0'))
	
	BMVert_dictionary = {}
	for i, vertex in enumerate(PolygonSoupVertices):
		BMVert = bm.verts.new(vertex)
		BMVert.index = i
		BMVert_dictionary[i] = BMVert
	
	for i, face in enumerate(PolygonSoupPolygons):
		muCollisionTag, mau8VertexIndices, mau8EdgeCosines = face
		mu16CollisionTag_part0, mu16CollisionTag_part1 = muCollisionTag
		
		if len(mau8VertexIndices) != len(set(mau8VertexIndices)):
			print("WARNING: collision face has duplicated vertices:", mau8VertexIndices)
			mau8VertexIndices = tuple(dict.fromkeys(mau8VertexIndices))
			print("adjusting to", mau8VertexIndices)
		
		if len(mau8VertexIndices) == 4:
			face_vertices = [BMVert_dictionary[mau8VertexIndices[0]], BMVert_dictionary[mau8VertexIndices[1]], BMVert_dictionary[mau8VertexIndices[3]], BMVert_dictionary[mau8VertexIndices[2]]]
		elif len(mau8VertexIndices) == 3:
			face_vertices = [BMVert_dictionary[mau8VertexIndices[0]], BMVert_dictionary[mau8VertexIndices[1]], BMVert_dictionary[mau8VertexIndices[2]]]
		else:
			print("WARNING: polygon vertices do not form a face. Skipping it.")
			continue
		
		BMFace = bm.faces.get(face_vertices) or bm.faces.new(face_vertices)
		if BMFace.index != -1:
			BMFace0 = BMFace
			BMFace = BMFace.copy(verts=False, edges=False)
			
			original_face_indices = [vert.index for vert in BMFace.verts]
			new_face_indices = [vert.index for vert in face_vertices]
			same_winding_faces_as_original = [original_face_indices[-n:] + original_face_indices[:-n] for n in range(0, len(original_face_indices))]
			if new_face_indices not in same_winding_faces_as_original:
				BMFace.normal_flip()
			
		BMFace.index = i
		BMFace[edge_cosine1] = mau8EdgeCosines[0]
		BMFace[edge_cosine2] = mau8EdgeCosines[1]
		BMFace[edge_cosine3] = mau8EdgeCosines[2]
		BMFace[edge_cosine4] = mau8EdgeCosines[3]
		BMFace[collision_tag0] = mu16CollisionTag_part0
		
		material_name = str(hex(mu16CollisionTag_part1))[2:].zfill(4).upper()
		mat = bpy.data.materials.get(material_name)
		if mat == None:
			mat = bpy.data.materials.new(material_name)
			mat.use_nodes = True
			mat.name = material_name
		
		if mat.name not in me_ob.materials:
			me_ob.materials.append(mat)
		
		BMFace.material_index = me_ob.materials.find(mat.name)
	
	bm.to_mesh(me_ob)
	bm.free()
	
	return obj


def create_bbox(BBoxSkin_object_name, mBBoxSkinData):
	mOrientation, maCornerSkinData, mCentreSkinData, mJointSkinData = mBBoxSkinData
	
	me_ob = bpy.data.meshes.new(BBoxSkin_object_name)
	obj = bpy.data.objects.new(BBoxSkin_object_name, me_ob)
	
	bm = bmesh.new()
	
	blend_index1 = (bm.verts.layers.int.get("blend_index1") or bm.verts.layers.int.new('blend_index1'))
	blend_index2 = (bm.verts.layers.int.get("blend_index2") or bm.verts.layers.int.new('blend_index2'))
	blend_index3 = (bm.verts.layers.int.get("blend_index3") or bm.verts.layers.int.new('blend_index3'))
	
	blend_weight1 = (bm.verts.layers.float.get("blend_weight1") or bm.verts.layers.float.new('blend_weight1'))
	blend_weight2 = (bm.verts.layers.float.get("blend_weight2") or bm.verts.layers.float.new('blend_weight2'))
	blend_weight3 = (bm.verts.layers.float.get("blend_weight3") or bm.verts.layers.float.new('blend_weight3'))
	
	BMVert_dictionary = {}
	for i, mCornerSkinData in enumerate(maCornerSkinData):
		mVertex, mafWeights, mauBoneIndices = mCornerSkinData
		BMVert = bm.verts.new(mVertex[:3])
		BMVert.index = i
		BMVert_dictionary[i] = BMVert
		BMVert[blend_index1], BMVert[blend_index2], BMVert[blend_index3] = mauBoneIndices
		BMVert[blend_weight1], BMVert[blend_weight2], BMVert[blend_weight3] = [mafWeights[0]*100.0, mafWeights[1]*100.0, mafWeights[2]*100.0]
	
	bm.faces.new([BMVert_dictionary[0], BMVert_dictionary[1], BMVert_dictionary[3], BMVert_dictionary[2]])
	bm.faces.new([BMVert_dictionary[6], BMVert_dictionary[7], BMVert_dictionary[5], BMVert_dictionary[4]])
	bm.faces.new([BMVert_dictionary[4], BMVert_dictionary[5], BMVert_dictionary[1], BMVert_dictionary[0]])
	bm.faces.new([BMVert_dictionary[2], BMVert_dictionary[3], BMVert_dictionary[7], BMVert_dictionary[6]])
	bm.faces.new([BMVert_dictionary[0], BMVert_dictionary[2], BMVert_dictionary[6], BMVert_dictionary[4]])
	bm.faces.new([BMVert_dictionary[5], BMVert_dictionary[7], BMVert_dictionary[3], BMVert_dictionary[1]])
	
	mVertex, mafWeights, mauBoneIndices = mCentreSkinData
	BMVert = bm.verts.new(mVertex[:3])
	BMVert.index = i
	BMVert[blend_index1], BMVert[blend_index2], BMVert[blend_index3] = mauBoneIndices
	BMVert[blend_weight1], BMVert[blend_weight2], BMVert[blend_weight3] = [mafWeights[0]*100.0, mafWeights[1]*100.0, mafWeights[2]*100.0]
	# It is also the position of the object's origin
	
	mVertex, mafWeights, mauBoneIndices = mJointSkinData
	BMVert = bm.verts.new(mVertex[:3])
	BMVert.index = i
	BMVert[blend_index1], BMVert[blend_index2], BMVert[blend_index3] = mauBoneIndices
	BMVert[blend_weight1], BMVert[blend_weight2], BMVert[blend_weight3] = [mafWeights[0]*100.0, mafWeights[1]*100.0, mafWeights[2]*100.0]
	
	bm.to_mesh(me_ob)
	bm.free()
	
	return obj


def create_pane(glass_object_name, GlassPaneData):
	glasspane_0x00, glasspane_0x10, glasspane_0x50, glasspane_0x58, glasspane_0x5C, glasspane_0x5E, glasspane_0x60, mePartType = GlassPaneData
	
	me_ob = bpy.data.meshes.new(glass_object_name)
	obj = bpy.data.objects.new(glass_object_name, me_ob)
	
	bm = bmesh.new()
	BMVert_dictionary = {}
	
	i = 0
	BMVert = bm.verts.new(glasspane_0x10[0][:3])
	BMVert.index = i
	BMVert_dictionary[i] = BMVert
	
	i = 1
	BMVert = bm.verts.new(glasspane_0x10[1][:3])
	BMVert.index = i
	BMVert_dictionary[i] = BMVert
	
	i = 2
	BMVert = bm.verts.new(glasspane_0x10[2][:3])
	BMVert.index = i
	BMVert_dictionary[i] = BMVert
	
	i = 3
	BMVert = bm.verts.new(glasspane_0x10[3][:3])
	BMVert.index = i
	BMVert_dictionary[i] = BMVert
	
	bm.faces.new([BMVert_dictionary[0], BMVert_dictionary[1], BMVert_dictionary[3], BMVert_dictionary[2]])
	
	bm.to_mesh(me_ob)
	bm.free()
	
	return obj


def get_triangle_from_trianglestrip(TriStrip, vertices_count):
	indices_buffer = []
	cte = 0
	for i in range(2, len(TriStrip)):
		if TriStrip[i] == 65535 or TriStrip[i-1] == 65535 or TriStrip[i-2] == 65535:
			if i%2==0:
				cte = -1
			else:
				cte = 0
			pass
		else:
			if (i+cte)%2==0:
				a = TriStrip[i-2]
				b = TriStrip[i-1]
				c = TriStrip[i]
			else:
				a = TriStrip[i-1]
				b = TriStrip[i-2]
				c = TriStrip[i]
			if a != b and b != c and c != a:
				if (a < vertices_count) and (b < vertices_count) and (c < vertices_count):
					indices_buffer.append([a, b, c])
	return indices_buffer


def get_tag_point_type(TagPointCode):
	TagPointTypes = {0x0: 'E_TAGPOINT_PHYSICS_CENTREOFMASS',
					0x1: 'E_TAGPOINT_LIGHTS_FRONTRUNNINGLEFT',
					0x2: 'E_TAGPOINT_LIGHTS_FRONTRUNNINGRIGHT',
					0x3: 'E_TAGPOINT_LIGHTS_REARRUNNINGLEFT',
					0x4: 'E_TAGPOINT_LIGHTS_REARRUNNINGRIGHT',
					0x5: 'E_TAGPOINT_LIGHTS_FRONTSPOTLEFT',
					0x6: 'E_TAGPOINT_LIGHTS_FRONTSPOTRIGHT',
					0x7: 'E_TAGPOINT_LIGHTS_INDICATORFRONTLEFT',
					0x8: 'E_TAGPOINT_LIGHTS_INDICATORFRONTRIGHT',
					0x9: 'E_TAGPOINT_LIGHTS_INDICATORREARLEFT',
					0xA: 'E_TAGPOINT_LIGHTS_INDICATORREARRIGHT',
					0xB: 'E_TAGPOINT_LIGHTS_BRAKELEFT',
					0xC: 'E_TAGPOINT_LIGHTS_BRAKERIGHT',
					0xD: 'E_TAGPOINT_LIGHTS_BRAKECENTRE',
					0xE: 'E_TAGPOINT_LIGHTS_REVERSELEFT',
					0xF: 'E_TAGPOINT_LIGHTS_REVERSERIGHT',
					0x10: 'E_TAGPOINT_LIGHTS_SPOTLIGHT1',
					0x11: 'E_TAGPOINT_LIGHTS_SPOTLIGHT2',
					0x12: 'E_TAGPOINT_LIGHTS_BLUESTWOS1',
					0x13: 'E_TAGPOINT_LIGHTS_BLUESTWOS2',
					0x14: 'E_TAGPOINT_TYREWELL_FRONTLEFT',
					0x15: 'E_TAGPOINT_TYREWELL_FRONTRIGHT',
					0x16: 'E_TAGPOINT_TYREWELL_REARLEFT',
					0x17: 'E_TAGPOINT_TYREWELL_REARRIGHT',
					0x18: 'E_TAGPOINT_TYREWELL_ADDITIONALLEFT',
					0x19: 'E_TAGPOINT_TYREWELL_ADDITIONALRIGHT',
					0x1A: 'E_TAGPOINT_AXLEPOINT_FRONT',
					0x1B: 'E_TAGPOINT_AXLEPOINT_REAR',
					0x1C: 'E_TAGPOINT_ARTICULATIONPOINT_FRONT',
					0x1D: 'E_TAGPOINT_ARTICULATIONPOINT_REAR',
					0x1E: 'E_TAGPOINT_ATTACHPOINT',
					0x1F: 'E_TAGPOINT_FXGLASSSMASHPOINT1',
					0x20: 'E_TAGPOINT_FXGLASSSMASHPOINT2',
					0x21: 'E_TAGPOINT_FXGLASSSMASHPOINT3',
					0x22: 'E_TAGPOINT_FXGLASSSMASHPOINT4',
					0x23: 'E_TAGPOINT_FXGLASSSMASHPOINT5',
					0x24: 'E_TAGPOINT_FXGLASSSMASHPOINT6',
					0x25: 'E_TAGPOINT_FXGLASSSMASHPOINT7',
					0x26: 'E_TAGPOINT_FXGLASSSMASHPOINT8',
					0x27: 'E_TAGPOINT_FXGLASSSMASHPOINT9',
					0x28: 'E_TAGPOINT_FXGLASSSMASHPOINT10',
					0x29: 'E_TAGPOINT_FXBOOSTPOINT1',
					0x2A: 'E_TAGPOINT_FXBOOSTPOINT2',
					0x2B: 'E_TAGPOINT_FXBOOSTPOINT3',
					0x2C: 'E_TAGPOINT_FXBOOSTPOINT4',
					0x2D: 'E_TAGPOINT_FXFIREPOINT',
					0x2E: 'E_TAGPOINT_FXSTEAMPOINT',
					0x2F: 'E_TAGPOINT_FXPOV_FRONTLEFT',
					0x30: 'E_TAGPOINT_FXPOV_FRONTRIGHT',
					0x31: 'E_TAGPOINT_FXPOV_REARLEFT',
					0x32: 'E_TAGPOINT_FXPOV_REARRIGHT',
					0x33: 'E_TAGPOINT_FXDASHBOARD',
					0x34: 'E_TAGPOINT_FXENGINE',
					0x35: 'E_TAGPOINT_FXTRUNK',
					0x36: 'E_TAGPOINT_FXPETROL_TANK',
					0x37: 'E_TAGPOINT_FXPELVIS_FRONTLEFT',
					0x38: 'E_TAGPOINT_PAYLOAD',
					0x39: 'E_TAGPOINT_COUNT'}
	
	if TagPointCode in TagPointTypes:
		return TagPointTypes[TagPointCode]
	
	return TagPointCode


def get_vertex_semantic(semantic_type):	#ok, missing type for 0x3 (PSIZE?, 5D_11_A3_74), and maybe 0xC and 0xF
	semantics = ["POSITION", "BLENDWEIGHT", "NORMAL", "", "", "", "", "BLENDINDICES",
				 "TEXCOORD1", "TEXCOORD2", "", "", "", "",
				 "TANGENT", ""]
	
	return semantics[semantic_type]


def get_vertex_data_type(data_type0, data_type1):
	#https://docs.microsoft.com/en-us/windows/win32/direct3d9/d3ddecltype
	data_type = ["B", 0x0]
	
	if data_type0 == 0x6:
		data_type = ["%dpacked" %data_type1, 0x4*data_type1]
	
	elif data_type0 == 0x2:
		data_type = ["%df" %data_type1, 0x4*data_type1]
	
	elif data_type0 == 0x3:
		data_type = ["%de" %data_type1, 0x2*data_type1]
	
	elif data_type0 == 0x4: # 255 normalized
		data_type = ["%dB" %data_type1, 0x1*data_type1]
	
	elif data_type0 == 0x7:
		data_type = ["%dB" %data_type1, 0x1*data_type1]
	
	else:
		print("WARNING: unsupported data_type0 found in vertex description [%d, %d]." % (data_type0, data_type1))
	
	return data_type


def get_part_type(PartCode):
	PartTypes = {0x0: 'eBody_Roof_PLAYERONLY',
				 0x1: 'eBody_BumperFront',
				 0x2: 'eBody_BumperRear',
				 0x3: 'eBody_Bonnet',
				 0x4: 'eBody_Boot',
				 0x5: 'eBody_Spoiler',
				 0x6: 'eBody_GrillFront',
				 0x7: 'eBody_GrillRear',
				 0x8: 'eBody_DoorLeft',
				 0x9: 'eBody_DoorLeftMirror',
				 0xA: 'eBody_DoorRight',
				 0xB: 'eBody_DoorRightMirror',
				 0xC: 'eBody_DoorRearLeft',
				 0xD: 'eBody_DoorRearRight',
				 0xE: 'eBody_DoorBackLeft',
				 0xF: 'eBody_DoorBackRight',
				 0x10: 'eBody_GlassDoorFrontLeft',
				 0x11: 'eBody_GlassDoorFrontRight',
				 0x12: 'eBody_GlassDoorRearLeft',
				 0x13: 'eBody_GlassDoorRearRight',
				 0x14: 'eBody_GlassWindscreenFront',
				 0x15: 'eBody_GlassWindscreenRear',
				 0x16: 'eBody_GlassPanelLeft_bus',
				 0x17: 'eBody_GlassPanelRight_bus',
				 0x18: 'eBody_SkirtLeft',
				 0x19: 'eBody_SkirtRight',
				 0x1A: 'eBody_WingFrontLeft',
				 0x1B: 'eBody_WingFrontRight',
				 0x1C: 'eBody_WingRearRight',
				 0x1D: 'eBody_WingRearLeft',
				 0x1E: 'eBody_Wiper1',
				 0x1F: 'eBody_Wiper2',
				 0x20: 'eBody_Wiper3',
				 0x21: 'eBody_MudFlapFrontLeft',
				 0x22: 'eBody_MudFlapFrontRight',
				 0x23: 'eBody_MudFlapRearLeft',
				 0x24: 'eBody_MudFlapRearRight',
				 0x25: 'eBody_Aerial',
				 0x26: 'eBody_NumberPlateRear',
				 0x27: 'eBody_NumberPlateFront',
				 0x28: 'eLights_FrontLeft',
				 0x29: 'eLights_FrontRight',
				 0x2A: 'eLights_RearLeft',
				 0x2B: 'eLights_RearRight',
				 0x2C: 'eLights_SpecialSiren',
				 0x2D: 'eChassis_FrontEnd',
				 0x2E: 'eChassis_PassengerCell',
				 0x2F: 'eChassis_RearEnd',
				 0x30: 'eChassis_ArmFrontRight',
				 0x31: 'eChassis_ArmFrontLeft',
				 0x32: 'eChassis_ArmRearRight',
				 0x33: 'eChassis_ArmRearLeft',
				 0x34: 'eChassis_ArmAdditionalR_Truck',
				 0x35: 'eChassis_ArmAdditionalL_Truck',
				 0x36: 'eChassis_WheelArchFrontLeft',
				 0x37: 'eChassis_WheelArchFrontRight',
				 0x38: 'eChassis_WheelArchRearLeft',
				 0x39: 'eChassis_WheelArchRearRight',
				 0x3A: 'eChassis_DiscFrontLeft',
				 0x3B: 'eChassis_DiscFrontRight',
				 0x3C: 'eChassis_DiscRearLeft',
				 0x3D: 'eChassis_DiscRearRight',
				 0x3E: 'eChassis_DiscAdditionalRight_Truck',
				 0x3F: 'eChassis_DiscAdditionalLeft_Truck',
				 0x40: 'eChassis_DiscCaliperFrontLeft',
				 0x41: 'eChassis_DiscCaliperFrontRight',
				 0x42: 'eChassis_DiscCaliperRearLeft',
				 0x43: 'eChassis_DiscCaliperRearRight',
				 0x44: 'eAncillaries_Block',
				 0x45: 'eAncillaries_Intercooler',
				 0x46: 'eAncillaries_Radiator',
				 0x47: 'eAncillaries_Battery',
				 0x48: 'eAncillaries_Fan',
				 0x49: 'eAncillaries_AirFilter',
				 0x4A: 'eAncillaries_Distributor',
				 0x4B: 'eAncillaries_InletManifold',
				 0x4C: 'eAncillaries_BrakeServo',
				 0x4D: 'eAncillaries_PlasticBox1',
				 0x4E: 'eAncillaries_PlasticBox2',
				 0x4F: 'eAncillaries_PlasticBox3',
				 0x50: 'eAncillaries_FluidResevoir1',
				 0x51: 'eAncillaries_FluidResevoir2',
				 0x52: 'eAncillaries_Pipe1',
				 0x53: 'eAncillaries_Pipe2',
				 0x54: 'eAncillaries_ExhaustSystem1',
				 0x55: 'eAncillaries_ExhaustSystem2',
				 0x56: 'eAncillaries_PetrolTank_Truck',
				 0x57: 'eWheels_FrontLeft',
				 0x58: 'eWheels_FrontRight',
				 0x59: 'eWheels_RearLeft',
				 0x5A: 'eWheels_RearRight',
				 0x5B: 'eWHEEL',
				 0x5C: 'eDISC',
				 0x5D: 'eCALIPER',
				 0x5E: 'eWheels_AdditionalRight_Truck',
				 0x5F: 'eWheels_AdditionalLeft_Truck',
				 0x60: 'eInterior_SeatFrontLeft',
				 0x61: 'eInterior_SeatFrontRight',
				 0x62: 'eInterior_SeatRearLeft',
				 0x63: 'eInterior_SeatRearRight',
				 0x64: 'eInterior_SeatRearBench',
				 0x65: 'eInterior_SeatAdditional_bus',
				 0x66: 'eInterior_SteeringWheel',
				 0x67: 'eInterior_InteriorMirror',
				 0x68: 'eInterior_SunVisorLeft',
				 0x69: 'eInterior_SunVisorRight',
				 0x6A: 'eInterior_Extinguisher',
				 0x6B: 'eVariation_RoofRacks',
				 0x6C: 'eVariation_BumperFrontAttachment1',
				 0x6D: 'eVariation_BumperFrontAttachment2',
				 0x6E: 'eVariation_BumperFrontAttachment3',
				 0x6F: 'eVariation_BumperFrontAttachment4',
				 0x70: 'eVariation_BumperRearAttachment1',
				 0x71: 'eVariation_BumperRearAttachment2',
				 0x72: 'eVariation_BumperRearAttachment3',
				 0x73: 'eVariation_BumperRearAttachment4',
				 0x74: 'eVariation_Luggage1',
				 0x75: 'eVariation_Luggage2',
				 0x76: 'eVariation_SpareWheel',
				 0x77: 'eVariation_Aerial',
				 0x78: 'eVariation_Ladder',
				 0x79: 'eVariation_Spotlights1',
				 0x7A: 'eVariation_SpotLights2',
				 0x7B: 'eVariation_AttachmentLeftSide1',
				 0x7C: 'eVariation_AttachmentLeftSide2',
				 0x7D: 'eVariation_AttachmentRightSide1',
				 0x7E: 'eVariation_AttachmentRightSide2',
				 0x7F: 'eVariation_Crane',
				 0x80: 'eVariation_Mixer',
				 0x81: 'eVariation_Tipper',
				 0x82: 'eVariation_Additional1',
				 0x83: 'eVariation_Additional2',
				 0x84: 'eWHEEL_BLURRED',
				 0x85: 'eBodyPartCount'}
	
	if PartCode in PartTypes:
		return PartTypes[PartCode]
	
	return PartCode


def get_joint_type(JointCode):
	JointTypes = {0x0: 'eNone',
				  0x1: 'eHinge',
				  0x2: 'eBallAndSocket',
				  0x3: 'eJointTypeCount'}
	
	if JointCode in JointTypes:
		return JointTypes[JointCode]
	
	return JointCode


def get_fourcc(dxgi_format):
	fourcc = { 0x81: "B8",
			   0x82: "A1R5G5B5",
			   0x83: "A4R4G4B4",
			   0x84: "R5G6B5",
			   0x85: "A8R8G8B8",
			   0x86: "COMPRESSED_DXT1",
			   0x86: "DXT1",
			   0x87: "COMPRESSED_DXT23",
			   0x87: "DXT3",
			   0x88: "COMPRESSED_DXT45",
			   0x88: "DXT5",
			   0x8B: "G8B8",
			   0x8F: "R6G5B5",
			   0x90: "D24S8",
			   0x91: "D24S8F",
			   0x91: "D24FS8",
			   0x92: "D16",
			   0x93: "D16F",
			   0x94: "R16",
			   0x94: "X16",
			   0x95: "G16R16",
			   0x95: "Y16_X16",
			   0x97: "R5G5B5A1",
			   0x98: "COMPRESSED_HILO8",
			   0x99: "COMPRESSED_HILO_S8",
			   0x9A: "W16_Z16_Y16_X16_FLOAT",
			   0x9A: "A16B16G16R16F",
			   0x9B: "W32_Z32_Y32_X32_FLOAT",
			   0x9B: "A32B32G32R32F",
			   0x9C: "R32F",
			   0x9C: "X32_FLOAT",
			   0x9D: "D1R5G5B5",
			   0x9D: "X1R5G5B5",
			   0x9E: "X8R8G8B8",
			   0x9E: "D8R8G8B8",
			   0x9F: "Y16_X16_FLOAT",
			   0x9F: "G16R16F",
			   0xFF: "NA" }
	
	return fourcc[dxgi_format]


def calculate_padding(lenght, alignment):
	division1 = (lenght/alignment)
	division2 = math.ceil(lenght/alignment)
	padding = int((division2 - division1)*alignment)
	return padding


def bytes_to_id(id):
	id = binascii.hexlify(id)
	id = str(id,'ascii')
	id = id.upper()
	id = '_'.join([id[x : x+2] for x in range(0, len(id), 2)])
	return id


def decode_resource_id(mResourceId, resource_type):
	mResource = mResourceId
	if resource_type == "GraphicsSpec" or resource_type == "GraphicsStub" or resource_type == "StreamedDeformationSpec":
		mResource, vehicle_main_ids = car_ids(swap_resource_id(mResourceId).replace('_', ''))
		if mResource == "NotFound":
			mResource, vehicle_main_ids = car_ids(mResourceId.replace('_', ''))
			if mResource == "NotFound":
				mResource = mResourceId
	
	elif resource_type == "InstanceList":
		for i in range(0, 1500):
			string = "TRK_UNIT%d_LIST" % i
			ID = hex(zlib.crc32(string.lower().encode()) & 0xffffffff)
			ID = ID[2:].upper().zfill(8)
			ID = '_'.join([ID[::-1][x:x+2][::-1] for x in range(0, len(ID), 2)]).lower()
			IDswap = swap_resource_id(ID)
			if (ID == mResourceId.lower()) or (IDswap == mResourceId.lower()):
				mResource = "TRK_UNIT%03d" % i
				break
	
	elif resource_type == "PolygonSoupList":
		for i in range(0, 1500):
			string = "TRK_COL_%d" % i
			ID = hex(zlib.crc32(string.lower().encode()) & 0xffffffff)
			ID = ID[2:].upper().zfill(8)
			ID = '_'.join([ID[::-1][x:x+2][::-1] for x in range(0, len(ID), 2)]).lower()
			IDswap = swap_resource_id(ID)
			if (ID == mResourceId.lower()) or (IDswap == mResourceId.lower()):
				mResource = "TRK_COL_%03d" % i
				break
	
	elif resource_type == "WheelGraphicsSpec":
		mResource, id = wheel_ids(swap_resource_id(mResourceId).replace('_', ''))
		if mResource == "NotFound":
			mResource, id = wheel_ids(mResourceId.replace('_', ''))
			if mResource == "NotFound":
				mResource = mResourceId
	
	if mResource == mResourceId:
		print("WARNING: could not decode the Id of the resource %s of type %s." %(mResourceId, resource_type))
	
	return mResource


def calculate_resourceid(resource_name):
	ID = hex(zlib.crc32(resource_name.lower().encode()) & 0xffffffff)
	ID = ID[2:].upper().zfill(8)
	#ID = '_'.join([ID[::-1][x:x+2][::-1] for x in range(0, len(ID), 2)])
	ID = '_'.join([ID[x:x+2] for x in range(0, len(ID), 2)])
	return ID


def swap_resource_id(mResourceId):
	mResourceId = mResourceId.replace('_', '')
	mResourceId = mResourceId[::-1]
	mResourceId = '_'.join([mResourceId[x:x+2][::-1] for x in range(0, len(mResourceId), 2)])
	return mResourceId


def car_ids(ID):
	#{'CarName' : ['GraphicsStubID', 'GraphicsSpecID', 'AttribSysVaultID', 'DeformationSpecID', 'VehicleAnimationID', 'BodypartRemappingID', 'AnimationCollectionID', 'CommsToolListID']}
	CarList = {'CARBB1GT' : ['81002E6D', '299FBED2', 'DC6E9D98', '5807B87B', 'F675C9EC', '79D41AF9', '2ACB1A65', 'ED4FCD7A'],
		'CARBB2CC' : ['61458BAC', 'CAA48BD0', '25E89CA1', 'C1B385E4', '2564DA88', '60C7A381', 'F9DA0901', '77B1349F'],
		'CARBEAGT' : ['C61C4E1E', '7DC3B693', '6DF3DAF4', 'E976B6C4', 'F9EB8EDD', 'D7340AD0', '25555D54', 'E459A68B'],
		'CARBMC04' : ['EEC2903A', '8841B1EA', '7CF27439', '42E59F05', 'C99359CD', '4D5E08DD', '152D8A44', '662FB0CE'],
		'CARBRWDS' : ['13B21A62', '9B56D9C2', 'B5DBE2BD', '6FEABE81', 'C8D61683', 'AF0BCE96', '1468C50A', '602F8AEB'],
		'CARBSC04' : ['DB0A35FC', 'E2EB50A4', '909B5D94', '0005A1FC', '2A0A5BA9', '547D39B4', 'F6B48820', 'CA0F767E'],
		'PASBCC01' : ['58D700A7', '6D9F4E0B', '551BF5E9', '7CF094D8', '3CCC159D', '3D972694', 'E072C614', 'B7496D67'],
		'PASBCC0C' : ['6255D6CE', '18C9AFB6', 'B07F27C9', '329CBF46', 'C06553DC', '960BF5D6', '1CDB8055', '6F7908E2'],
		'PASBCC0G' : ['F43F6F0E', '626944BF', '320CFE79', 'FDBBB735', 'D627C247', '56AD7523', '0A9911CE', '76BD65E5'],
		'PASBCCA2' : ['7D91CEA0', '8A264959', '376BC9D7', '613172F0', '915C239E', 'BF365414', '4DE2F017', '1874C45D'],
		'PASBCCA3' : ['F848587D', 'B44D8BB6', 'F7B44716', '22FAD477', '348F7F55', '0F1F3429', 'E831ACDC', '8E44C32A'],
		'PASBS01' : ['AB0E3528', '448336C4', '25FB88AB', '8D1B2911', '7223CB91', 'F6E1D2FC', 'AE9D1818', 'FD96DE45'],
		'PASBS0C' : ['918CE341', '31D5D779', 'C09F5A8B', 'C377028F', '8E8A8DD0', '5D7D01BE', '52345E59', '25A6BBC0'],
		'PASBS0G' : ['07E65A81', '4B753C70', '42EC833B', '0C500AFC', '98C81C4B', '9DDB814B', '4476CFC2', '3C62D6C7'],
		'PASBS1A2' : ['40FAF660', 'C3440E3D', '61D5ADD8', '974B4A3A', '5BEAE025', '0AFFA5DC', '875433AC', '59D9E562'],
		'PASBS1A3' : ['C52360BD', 'FD2FCCD2', 'A10A2319', 'D480ECBD', 'FE39BCEE', 'BAD6C5E1', '22876F67', 'CFE9E215'],
		'PASBSC01' : ['C6E92741', 'B73949BF', '3927478F', '595B5238', '4D8ED531', '16A69DE8', '913006B8', '281E7437'],
		'PASBSC0C' : ['FC6BF128', 'C26FA802', 'DC4395AF', '173779A6', 'B1279370', 'BD3A4EAA', '6D9940F9', 'F02E11B2'],
		'PASBSC0G' : ['6A0148E8', 'B8CF430B', '5E304C1F', 'D81071D5', 'A76502EB', '7D9CCE5F', '7BDBD162', 'E9EA7CB5'],
		'PASBSCA2' : ['E3AFE946', '50804EED', '5B577BB1', '449AB410', 'E01EE332', '9407EF68', '3CA030BB', '8723DD0D'],
		'PASBSCA3' : ['66767F9B', '6EEB8C02', '9B88F570', '07511297', '45CDBFF9', '242E8F55', '99736C70', '1113DA7A'],
		'PASC01' : ['BC7A59E3', '2A56F43F', 'AF757901', 'B48BE14A', 'C2F8F02E', 'C5476817', '1E4623A7', '5DBE31A3'],
		'PASC0C' : ['86F88F8A', '5F001582', '4A11AB21', 'FAE7CAD4', '3E51B66F', '6EDBBB55', 'E2EF65E6', '858E5426'],
		'PASC0G' : ['1092364A', '25A0FE8B', 'C8627291', '35C0C2A7', '281327F4', 'AE7D3BA0', 'F4ADF47D', '9C4A3921'],
		'PASC1A2' : ['F313EEE3', '49CAFF97', 'D14E6AD5', '0F0B1465', '0C623EEE', 'BA249E63', 'D0DCED67', '9995D5B4'],
		'PASC1A3' : ['76CA783E', '77A13D78', '1191E414', '4CC0B2E2', 'A9B16225', '0A0DFE5E', '750FB1AC', '0FA5D2C3'],
		'PBTEA01' : ['29793CF3', 'C636D62D', '9CF9D7A8', 'FDAB04C7', '95050AB0', 'C2B30089', '49BBD939', 'E4771FF3'],
		'PBTEA1B' : ['E0C373DA', '4DD47BBE', 'D60E2ED2', '11BADB31', '7874679C', '7CD5EF3D', 'A4CAB415', 'EB466618'],
		'PBTEA1C' : ['651AE507', '73BFB951', '16D1A013', '52717DB6', 'DDA73B57', 'CCFC8F00', '0119E8DE', '7D76616F'],
		'PBTHM01' : ['949283BF', '391BF06F', '3C309785', '37BD9C91', '8DF7EA16', '67CCA5D5', '5149399F', '5D566F08'],
		'PBTHM0B' : ['2BC9C30B', '7226D33D', '198BCB64', '3A1A1188', 'D48DF09C', '7C7916AA', '08332315', '13560DFA'],
		'PBTHM0C' : ['AE1055D6', '4C4D11D2', 'D95445A5', '79D1B70F', '715EAC57', 'CC507697', 'ADE07FDE', '85660A8D'],
		'PBTJPDI' : ['2EFA61ED', '7A2ABFFF', '276FD26A', 'E728BA4C', 'CFBCE5E8', 'FFF8F50E', '13023661', '63EFFF0D'],
		'PBTRT01' : ['069E079F', 'A80C1970', 'F97A8002', 'FB104EEB', '6215F04C', '993898CA', 'BEAB23C5', '59793C24'],
		'PBTRT0B' : ['B9C5472B', 'E3313A22', 'DCC1DCE3', 'F6B7C3F2', '3B6FEAC6', '828D2BB5', 'E7D1394F', '17795ED6'],
		'PBTRT0C' : ['3C1CD1F6', 'DD5AF8CD', '1C1E5222', 'B57C6575', '9EBCB60D', '32A44B88', '42026584', '814959A1'],
		'PBTSVK01' : ['A4267826', 'A89A1EED', '6F7D1D02', 'CC007BDD', '12FD6E3E', '5FCD1753', 'CE43BDB7', 'B52BD47F'],
		'PBTSVK02' : ['6A4AB29B', 'AB212906', '6E1BFF9B', '485BE18E', 'BC8FFAB8', '8FB7B714', '60312931', '0F7ADDE6'],
		'PBTTMC04' : ['5830B068', 'AB94383B', 'DB0AC29B', 'C047279B', 'C1B00F71', 'FC4CA8ED', '1D0EDCF8', '0C829534'],
		'PBTTMC2' : ['4AFD2618', '3E04264B', '8073D71B', '67815E8F', '6CC7B7C8', '8AE80B33', 'B0796441', '57E13F1A'],
		'PBTTMC3' : ['CF24B0C5', '006FE4A4', '40AC59DA', '244AF808', 'C914EB03', '3AC16B0E', '15AA388A', 'C1D1386D'],
		'PCCBC01' : ['1A63D27E', '45E31A06', 'D3E74DDC', 'EBFBDF67', '702AB292', '74EF3933', 'AC94611B', '0403D074'],
		'PCCBCC01' : ['B18D17FD', '41258CC8', '0CB5EEDB', 'D469F59C', '6896D8DF', '14AFE4EB', 'B4280B56', '055A24F3'],
		'PCCBH01' : ['E4C526A0', '4B478877', '7058843B', 'C76028CD', '2636D8CF', '8EBB3E31', 'FA880B46', 'E5EC8578'],
		'PCCBR01' : ['BD274B83', 'D642A791', '8C98DCB5', 'B9407FA3', 'C51BA322', '0E7890F2', '19A570AB', '43CA3469'],
		'PCCBS01' : ['55FCB03A', 'B90E020A', '09414A68', 'E1C09D74', '5B1B09EE', 'BA73E754', '87A5DA67', '74A0F668'],
		'PCCBSC01' : ['2FB3301B', '9B838B7C', '60895CBD', 'F1C2337C', '19D41873', '3F9E5F97', 'C56ACBFA', '9A0D3DA3'],
		'PCCC01' : ['E5D442D1', '5D349D6A', '52F84DCF', 'EC21E34E', '8E6AC586', '685E2545', '52D4160F', 'A2BAE889'],
		'PCCCC01' : ['8BF2BAD0', 'C03A8CDB', 'A5064241', 'ADC0B802', '333EC985', 'EAEF93FF', 'EF801A0C', '61646CCC'],
		'PCCCLT2' : ['3225ED61', 'DF74BE24', '1E39B5CC', '81AA98A3', '5B0F396A', 'A9ADB2DA', '87B1EAE3', 'E7F82CCA'],
		'PCCCO01' : ['6F5B4F95', '417786DE', '5EBFF8DB', 'CAD071E2', '7C2B66D2', '9E853338', 'A095B55B', '059D76C5'],
		'PCCCT01' : ['DE62D90F', 'B33E0CA3', '27A63688', 'EC70C45B', '0106B7F3', 'AA4DEA5D', 'DDB8647A', '94D105D5'],
		'PCCCV01' : ['4FD35FA7', '2CA0374F', '6C136AE8', '1D76702F', '7C0192B1', '835C75CA', 'A0BF4138', 'FA0581D6'],
		'PCCGA01' : ['9D0F0DAC', 'C9CE0EF7', 'F53CB238', '052DE138', '4268009A', '39F046EC', '9ED6D313', '58278A40'],
		'PCCLM01' : ['C48D23B3', 'EB3CCD15', 'E3BE30ED', '1AA65AEA', 'D0E3FA4F', '1B868C76', '0C5D29C6', '3D59919E'],
		'PCCLR01' : ['16D1C9A3', '664E416B', '0CCD477E', 'DE0B87BA', '57C061EA', '3C6A1AE7', '8B7EB263', '70BDEB89'],
		'PCCMC01' : ['200438F0', '70366A21', '2553D98A', 'CA8B401B', 'A1E50B4D', 'D8FD19EA', '7D5BD8C4', '5213B32C'],
		'PCCMC02' : ['EE68F24D', '738D5DCA', '24353B13', '4ED0DA48', '0F979FCB', '0887B9AD', 'D3294C42', 'E842BAB5'],
		'PCCMC04' : ['33B717ED', '34FD43C7', '67FF8EFB', '4667EEEF', '1274C61D', 'A872F922', 'CECA1594', 'DDE7D95C'],
		'PCCME01' : ['D2D0C2D2', '909357CE', 'F88C3C2A', 'D9809C86', '26EC648B', 'E2C8C989', 'FA52B702', 'E06F3E28'],
		'PCCMU3' : ['47E07799', 'D3824620', 'C38D07C5', '3AB6D550', '6983B4C8', '8AED4F30', 'B53D6741', 'C44D76E0'],
		'PCCPK01' : ['60B4DCD0', '2A864DD4', '7FCC9201', 'C73B7644', '325B61C3', '4597483E', 'EEE5B24A', 'A8CDD380'],
		'PCCRC01' : ['845DF598', '9F451DB2', 'BFDBFFBA', 'CE501987', '0168723E', '5FDE824F', 'DDD6A1B7', '9B54C924'],
		'PCCRC03' : ['CFE8A9F8', 'A295E8B6', '7E6293E2', '09C02553', '0AC9BA73', '3F8D4235', 'D67769FA', 'B735C7CA'],
		'PCCRG01' : ['E7388912', 'E07E1BB1', '29B1467A', '2C5D716E', 'FB6638BA', '4CFACDBB', '27D8EB33', '47FCC023'],
		'PCCRN01' : ['882FFB64', '7144B22C', 'C1BBD3FD', 'F1C032B0', 'D07D77A5', '9FBF552E', '0CC3A42C', 'C8C7112C'],
		'PCCRR01' : ['23196C65', '0CE4A025', 'E0A46ED3', '9CEBB943', 'B459638E', '25492B8E', '68E7B007', 'DC9D2D39'],
		'PCCS01' : ['AA4B2095', 'A1D98566', '885E4A7B', 'E61AA15D', 'A55B7EFA', 'A6C2FB22', '79E5AD73', 'D219CE95'],
		'PCCSC01' : ['15CC9D36', '1A9C8B6F', 'C93AF027', '886B7EE2', '427C0929', 'C1DE2883', '9EC2DAA0', 'FE33759C'],
		'PCCSC02' : ['DBA0578B', '1927BC84', 'C85C12BE', '0C30E4B1', 'EC0E9DAF', '11A488C4', '30B04E26', '44627C05'],
		'PCCSC03' : ['5E79C156', '274C7E6B', '08839C7F', '4FFB4236', '49DDC164', 'A18DE8F9', '956312ED', 'D2527B72'],
		'PCCSC04' : ['067FB22B', '5E57A289', '8B96A756', '0487D016', 'F1EDC479', 'B151C84B', '2D5317F0', '71C71FEC'],
		'PCCSR01' : ['B28804CB', '893D36F8', '9645614E', 'DAD0DE26', 'F74D1899', 'BB498142', '2BF3CB10', 'B9FA9181'],
		'PCCSV01' : ['D1ED7841', 'F60630FB', '002FD88E', '38DDB6CF', '0D43521D', 'A86DCEB6', 'D1FD8194', '65529886'],
		'PDDK01XS' : ['516C0E5F', '759DE692', '012B00FA', 'A7F97241', 'DF58C617', '26987B22', '03E6159E', '61896430'],
		'PDDK01' : ['5C9CA0C3', '3BEE2F74', 'E58E826B', 'A21CE1CF', '8B079DD3', 'DF746E18', '57B94E5A', 'B30F0CA8'],
		'PDDK0A' : ['2DAB2ACA', '73683BCD', 'C1533C13', '2BE0F685', '7C0F13DF', '14BB7D20', 'A0B1C056', '475E67C3'],
		'PDDK0C' : ['661E76AA', '4EB8CEC9', '00EA504B', 'EC70CA51', '77AEDB92', '74E8BD5A', 'AB10081B', '6B3F692D'],
		'PDLCB2F' : ['56E57ADB', 'B3E9188E', 'F0B21B88', 'DA1AC793', 'C5594717', '26827AA3', '19E7949E', 'EA0FC295'],
		'PDLCCVFA' : ['4FFF5667', '1CF45641', '9442BDCE', '60B08154', '2A0BAAAF', '11628DF3', 'F6B57926', '5335D267'],
		'PDLCCVL2' : ['6B7E2101', 'D391DAF1', 'D011D6C5', 'E2D2895F', '3D2EC081', '6CF4A52D', 'E1901308', '97DD5F6F'],
		'PDLCCVL3' : ['EEA7B7DC', 'EDFA181E', '10CE5804', 'A1192FD8', '98FD9C4A', 'DCDDC510', '44434FC3', '01ED5818'],
		'PDLCGB' : ['76F5BC89', '44BE862B', '184B67AB', '84561637', '4613C8D7', '59AC5C96', '9AAD1B5E', '39BD3364'],
		'PDLCGL' : ['C6F95A73', 'F78E4F35', '1E6011F9', '12AE3276', '3672C2ED', '38126C29', 'EACC1164', '3E908B83'],
		'PDLCML2' : ['31E551AA', 'D2A6BB66', '714046B2', 'A3694464', '6293922A', '43F225AE', 'BE2D41A3', 'E0ADA0D6'],
		'PDLCML3' : ['B43CC777', 'ECCD7989', 'B19FC873', 'E0A2E2E3', 'C740CEE1', 'F3DB4593', '1BFE1D68', '769DA7A1'],
		'PDLCMOR' : ['4151BD6B', '73C7E361', '6E8B9013', '35D184D3', '93832214', 'A4D84270', '4F3DF19D', 'B3BF518B'],
		'PDLCNR01' : ['2F6F2332', '323E632C', '917A0612', '5BD7FDDB', 'FD362496', 'F277037E', '2188F71F', '74EE3B15'],
		'PDRWT01' : ['9D48164C', 'FF200EB7', '82A948F7', 'A29F0844', '29EACCE3', '303F7CFC', 'F5541F6A', 'D69FFB4A'],
		'PDRWTL2' : ['E37E22FC', '1FD49D2E', '0ED8DB57', '5491459F', '441B2D81', '6C8D90C0', '98A5FE08', '34DCFCC5'],
		'PDRWTL3' : ['66A7B421', '21BF5FC1', 'CE075596', '175AE318', 'E1C8714A', 'DCA4F0FD', '3D76A2C3', 'A2ECFBB2'],
		'PDSHR01' : ['880E8781', '86174B56', '2D2570DE', '2BCC57DA', '300518B9', 'CE3D4C2D', 'ECBBCB30', '1D8D6C7B'],
		'PDSVK0B' : ['221572C1', 'CA5738DB', 'D65B97A1', 'B32DE5F7', '8ACCF434', 'D17288C9', '567227BD', '00353F2A'],
		'PDSVK0W' : ['EB005A68', '661DBF1A', '5F33367E', '42581A14', 'A25FEF67', '236A8861', '7EE13CEE', 'EBD1E247'],
		'PEUBR01' : ['4DB5523D', 'FEE12D2D', 'D5BAD580', '130D576C', '2920A6E0', 'B2335420', 'F59E7569', '7C4BCD50'],
		'PEUBR0C' : ['77378454', '8BB7CC90', '30DE07A0', '5D617CF2', 'D589E0A1', '19AF8762', '09373328', 'A47BA8D5'],
		'PEUBR0G' : ['E15D3D94', 'F1172799', 'B2ADDE10', '92467481', 'C3CB713A', 'D9090797', '1F75A2B3', 'BDBFC5D2'],
		'PEUBRA2' : ['68F39C3A', '19582A7F', 'B7CAE9BE', '0ECCB144', '84B090E3', '309226A0', '580E436A', 'D376646A'],
		'PEUBRA3' : ['ED2A0AE7', '2733E890', '7715677F', '4D0717C3', '2163CC28', '80BB469D', 'FDDD1FA1', '4546631D'],
		'PEUGTB2' : ['57DF5E1E', 'EB28DA14', 'F7A931ED', '60CA6118', 'D1E6805E', 'C0DB820D', '0D5853D7', '90A91A72'],
		'PEUGTB3' : ['D206C8C3', 'D54318FB', '3776BF2C', '2301C79F', '7435DC95', '70F2E230', 'A88B0F1C', '06991D05'],
		'PEULM01' : ['341F3A0D', 'C39F47A9', 'BA9C39D8', 'B0EB7225', '3CD8FF8D', 'A7CD48A4', 'E0662C04', '02D868A7'],
		'PEULM0C' : ['0E9DEC64', 'B6C9A614', '5FF8EBF8', 'FE8759BB', 'C071B9CC', '0C519BE6', '1CCF6A45', 'DAE80D22'],
		'PEULM0G' : ['98F755A4', 'CC694D1D', 'DD8B3248', '31A051C8', 'D6332857', 'CCF71B13', '0A8DFBDE', 'C32C6025'],
		'PEULMA2' : ['1159F40A', '242640FB', 'D8EC05E6', 'AD2A940D', '9148C98E', '256C3A24', '4DF61A07', 'ADE5C19D'],
		'PEULMA3' : ['948062D7', '1A4D8214', '18338B27', 'EEE1328A', '349B9545', '95455A19', 'E82546CC', '3BD5C6EA'],
		'PEUR3A2' : ['636DBBAF', '5C05EB60', 'F5BE40B8', '5B0B9D3E', '863067AA', 'D6DDE13E', '5A8EB423', 'BBC6254B'],
		'PEUR3A3' : ['E6B42D72', '626E298F', '3561CE79', '18C03BB9', '23E33B61', '66F48103', 'FF5DE8E8', '2DF6223C'],
		'PEURC03' : ['3F7AB046', '8A36620A', '27409AD7', 'A38D0D9C', 'E6F2BFB1', '83C686E7', '3A4C6C38', '88B43EF3'],
		'PEURC0C' : ['4E4D3A4F', 'C2B076B3', '039D24AF', '2A711AD6', '11FA31BD', '480995DF', 'CD44E234', '7CE55598'],
		'PEURC0G' : ['D827838F', 'B8109DBA', '81EEFD1F', 'E55612A5', '07B8A026', '88AF152A', 'DB0673AF', '6521389F'],
		'PEURG01' : ['17AA90AC', 'C8DD910D', '70934F4F', '861059A1', '175D3D78', 'F0B10969', 'CBE3EEF1', '787D391A'],
		'PEURG0C' : ['2D2846C5', 'BD8B70B0', '95F79D6F', 'C87C723F', 'EBF47B39', '5B2DDA2B', '374AA8B0', 'A04D5C9F'],
		'PEURG0G' : ['BB42FF05', 'C72B9BB9', '178444DF', '075B7A4C', 'FDB6EAA2', '9B8B5ADE', '2108392B', 'B9893198'],
		'PEURR01' : ['D38B75DB', '24472A99', 'B98667E6', '36A6918C', '5862664C', '9902EF5C', '84DCB5C5', 'E31CD400'],
		'PEURR0C' : ['E909A3B2', '5111CB24', '5CE2B5C6', '78CABA12', 'A4CB200D', '329E3C1E', '7875F384', '3B2CB185'],
		'PEURR0G' : ['7F631A72', '2BB1202D', 'DE916C76', 'B7EDB261', 'B289B196', 'F238BCEB', '6E37621F', '22E8DC82'],
		'PEURRA2' : ['F6CDBBDC', 'C3FE2DCB', 'DBF65BD8', '2B6777A4', 'F5F2504F', '1BA39DDC', '294C83C6', '4C217D3A'],
		'PEURRA3' : ['73142D01', 'FD95EF24', '1B29D519', '68ACD123', '50210C84', 'AB8AFDE1', '8C9FDF0D', 'DA117A4D'],
		'PEUS01' : ['D8ABA287', '10EBA58A', 'A0FDC0C7', 'D02979CF', '1910BA28', '808335EB', 'C5AE69A1', '31E4FC6F'],
		'PEUS0C' : ['E22974EE', '65BD4437', '459912E7', '9E455251', 'E5B9FC69', '2B1FE6A9', '39072FE0', 'E9D499EA'],
		'PEUS0G' : ['7443CD2E', '1F1DAF3E', 'C7EACB57', '51625A22', 'F3FB6DF2', 'EBB9665C', '2F45BE7B', 'F010F4ED'],
		'PEUS2A2' : ['1A2728B8', 'B690D826', '0686D9F8', '45B0188C', '5B24B671', 'FCD63C54', '879A65F8', 'E9CB5BF2'],
		'PEUS2A3' : ['9FFEBE65', '88FB1AC9', 'C6595739', '067BBE0B', 'FEF7EABA', '4CFF5C69', '22493933', '7FFB5C85'],
		'PEUS3A2' : ['F2FCD301', 'D9DC7DBD', '835F4F25', '1D30FA5B', 'C5241CBD', '48DD4BF2', '199ACF34', 'DEA199F3'],
		'PEUS3A3' : ['772545DC', 'E7B7BF52', '4380C1E4', '5EFB5CDC', '60F74076', 'F8F42BCF', 'BC4993FF', '48919E84'],
		'PEUS4A2' : ['E8F3D29A', '5635E5C9', 'DB593C58', '56BBC411', 'DC2DD9B7', 'C6E3EC37', '00930A3E', '5BB7D6F6'],
		'PEUS4A3' : ['6D2A4447', '685E2726', '1B86B299', '15706296', '79FE857C', '76CA8C0A', 'A54056F5', 'CD87D181'],
		'PEUS4B1' : ['FDBA795B', '54E830BB', '2AED40B6', 'B03DD8A8', 'EF45A500', 'B8EBD8F6', '33FB7689', '22B5F244'],
		'PEUS4B2' : ['33D6B3E6', '57530750', '2B8BA22F', '346642FB', '41373186', '689178B1', '9D89E20F', '98E4FBDD'],
		'PEUS4B3' : ['B60F253B', '6938C5BF', 'EB542CEE', '77ADE47C', 'E4E46D4D', 'D8B8188C', '385ABEC4', '0ED4FCAA'],
		'PEUS4BC' : ['C738AF32', '21BED106', 'CF899296', 'FE51F336', '13ECE341', '13770BB4', 'CF5230C8', 'FA8597C1'],
		'PEUS4BG' : ['515216F2', '5B1E3A0F', '4DFA4B26', '3176FB45', '05AE72DA', 'D3D18B41', 'D910A153', 'E341FAC6'],
		'PEUSA2' : ['FDED6C80', 'F752A2D8', 'C28DFCF9', 'CDE89FE7', 'B4808C2B', '0222476B', '683E5FA2', '9ED95555'],
		'PEUSA3' : ['7834FA5D', 'C9396037', '02527238', '8E233960', '1153D0E0', 'B20B2756', 'CDED0369', '08E95222'],
		'PEUSC02C' : ['DDFCBFC7', '4ABD50A8', '1CB05C4C', '5BCCE418', '269BBAB3', '400C7C8F', 'FA25693A', '38F252C1'],
		'PEUSC02G' : ['4B960607', '301DBBA1', '9EC385FC', '94EBEC6B', '30D92B28', '80AAFC7A', 'EC67F8A1', '21363FC6'],
		'PEUSC02' : ['2B324E35', '31843638', '917E1B8B', 'A67DCC7E', '0035986D', 'ADEF4C16', 'DC8B4BE4', '7BE3853C'],
		'PEUSC03' : ['AEEBD8E8', '0FEFF4D7', '51A1954A', 'E5B66AF9', 'A5E6C4A6', '1DC62C2B', '7958172F', 'EDD3824B'],
		'PEUSC04G' : ['FDDDC4FF', '73D70E49', '7E66B813', '11579065', '0AECFB4B', '9D49A5AC', 'D65228C2', 'A7916590'],
		'PEUSC04S' : ['B1117A8B', 'E1F64B67', '37D1970D', 'A3E9C901', '87ACBCD3', 'DF78C539', '5B126F5A', 'DA45BF8A'],
		'PEUSC04' : ['F6EDAB95', '76F42835', 'D2B4AE63', 'AECAF8D9', '1DD6C1BB', '0D1A0C99', 'C1681232', '4E46E6D5'],
		'PEUSC0C' : ['DFDC52E1', '4769E06E', '757C2B32', '6C4A7DB3', '52EE4AAA', 'D6093F13', '8E509923', '1982E920'],
		'PEUSC0G' : ['49B6EB21', '3DC90B67', 'F70FF282', 'A36D75C0', '44ACDB31', '16AFBFE6', '981208B8', '00468427'],
		'PEUSR01' : ['421A1D75', 'A19EBC44', 'CF67687B', '709DF6E9', '1B761D5B', '07024590', 'C7C8CED2', '867B68B8'],
		'PEUSR0C' : ['7898CB1C', 'D4C85DF9', '2A03BA5B', '3EF1DD77', 'E7DF5B1A', 'AC9E96D2', '3B618893', '5E4B0D3D'],
		'PEUSR0G' : ['EEF272DC', 'AE68B6F0', 'A87063EB', 'F1D6D504', 'F19DCA81', '6C381627', '2D231908', '478F603A'],
		'PEUSRA2' : ['675CD372', '4627BB16', 'AD175445', '6D5C10C1', 'B6E62B58', '85A33710', '6A58F8D1', '2946C182'],
		'PEUSRA3' : ['E28545AF', '784C79F9', '6DC8DA84', '2E97B646', '13357793', '358A572D', 'CF8BA41A', 'BF76C6F5'],
		'PEUSV01' : ['217F61FF', 'DEA5BA47', '590DD1BB', '92909E00', 'E17857DF', '14260A64', '3DC68456', '5AD361BF'],
		'PEUSV0C' : ['1BFDB796', 'ABF35BFA', 'BC69039B', 'DCFCB59E', '1DD1119E', 'BFBAD926', 'C16FC217', '82E3043A'],
		'PEUSV0G' : ['8D970E56', 'D153B0F3', '3E1ADA2B', '13DBBDED', '0B938005', '7F1C59D3', 'D72D538C', '9B27693D'],
		'PEUSVA2' : ['0439AFF8', '391CBD15', '3B7DED85', '8F517828', '4CE861DC', '968778E4', '9056B255', 'F5EEC885'],
		'PEUSVA3' : ['81E03925', '07777FFA', 'FBA26344', 'CC9ADEAF', 'E93B3D17', '26AE18D9', '3585EE9E', '63DECFF2'],
		'PSD88S' : ['F7CD0F85', 'B3C6391C', 'DF938988', 'A282D58E', '3F8C39BC', '0921920C', 'E332EA35', '7C7E3D44'],
		'PSDBC01' : ['4943E370', 'CAD6B527', '57D66BA1', 'F237CFA7', 'C2F598DE', '5503F670', '1E4B4B57', '8FDD26C5'],
		'PSDCCO01' : ['78DE28CD', '32B8AF2D', '17B60712', '21424D87', '66109642', '910E1577', 'BAAE45CB', 'A72685BD'],
		'PSDCV01' : ['1CF36EA9', 'A395986E', 'E8224C95', '04BA60EF', 'CEDEB8FD', 'A2B0BA89', '12606B74', '71DB7767'],
		'PSDGB' : ['C2B7B579', 'DF3743B3', '5DC422CC', 'B29F67BA', '043D1EF6', '6D5B86F4', 'D883CD7F', '4886A480'],
		'PSDGL01' : ['C25D325E', 'A8FA0E48', '0F6DB802', '2371DACF', '21A22F4D', 'D87D5ECE', 'FD1CFCC4', '806AA4F9'],
		'PSDGP' : ['53A4EEAD', '0A661890', '57B9B83A', '08960A79', '949E00B8', '8F9FA6EE', '4820D331', '00F71D73'],
		'PSDMC01' : ['732409FE', 'FF03C500', 'A162FFF7', 'D34750DB', '133A2101', 'F911D6A9', 'CF84F288', 'D9CD459D'],
		'PSDMC04' : ['609726E3', 'BBC8ECE6', 'E3CEA886', '5FABFE2F', 'A0ABEC51', '899E3661', '7C153FD8', '56392FED'],
		'PSDNR01' : ['26D4582A', 'A2CEB22A', '25380FE2', '4BB159B0', '6337BD88', '6081F0E6', 'BF896E01', '70AB1492'],
		'PSDPK01' : ['3394EDDE', 'A5B3E2F5', 'FBFDB47C', 'DEF76684', '80844B8F', '647B877D', '5C3A9806', '23132531'],
		'PSDRI01' : ['C100CBF1', '71988579', '1D8C86FD', 'A3871C3A', '7BAB98E3', '306D3DA8', 'A7154B6A', 'C60FA898'],
		'PSDSC01' : ['46ECAC38', '95A9244E', '4D0BD65A', '91A76E22', 'F0A32365', 'E032E7C0', '2C1DF0EC', '75ED832D'],
		'PSPBEST' : ['9BD93AAB', '5773AF80', '0B23722F', 'CC0EED9A', 'EC29C41C', 'E98AD5FB', '30971795', 'A6392989'],
		'PSPBZ' : ['34560CDD', '028C73F9', '8F5A0A34', '5E1EF655', '84AD52B3', '40AE4A67', '5813813A', 'F7E190F5'],
		'PSPCIR' : ['4C0EE680', '279D9C73', 'D961847F', '0ADF9928', '7441A70B', '7751032F', 'A8FF7482', '6623082F'],
		'PSPGAS' : ['9CAC55E4', '232C9B25', '71A2BF78', 'A7B70651', '4CD25E77', 'B9DE7F0A', '906C8DFE', '2431DF97'],
		'PSPMETL' : ['D66119AE', 'FD729DBA', 'FC5B4B19', '6AA21DF6', '45585FE9', 'BE74606F', '99E68C60', '6127678D'],
		'PSPMICR' : ['F4F472A6', '6F5F3D01', 'B909F107', '9A852C8F', 'A18C5525', '0A05C369', '7D3286AC', 'F067F17B'],
		'PSPWAL' : ['3C404033', 'BA1B26FF', 'A634B6F1', '05269793', '295365F9', '2442118F', 'F5EDB670', 'A19FF106'],
		'PUSBC01' : ['FA1A5C49', '94943006', 'E62F992D', 'C6F93DF7', '10A55FF3', 'AA5C49B5', 'CC1B8C7A', '0075BFC1'],
		'PUSBC0C' : ['C0988A20', 'E1C2D1BB', '034B4B0D', '88951669', 'EC0C19B2', '01C09AF7', '30B2CA3B', 'D845DA44'],
		'PUSBC0G' : ['56F233E0', '9B623AB2', '813892BD', '47B21E1A', 'FA4E8829', 'C1661A02', '26F05BA0', 'C181B743'],
		'PUSBCA2' : ['DF5C924E', '732D3754', '845FA513', 'DB38DBDF', 'BD3569F0', '28FD3B35', '618BBA79', 'AF4816FB'],
		'PUSBCA3' : ['5A850493', '4D46F5BB', '44802BD2', '98F37D58', '18E6353B', '98D45B08', 'C458E6B2', '3978118C'],
		'PUSBH01' : ['04BCA897', '9A30A277', '459050CA', 'EA62CA5D', '46B935AE', '50084EB7', '9A07E627', 'E19AEACD'],
		'PUSBH0C' : ['3E3E7EFE', 'EF6643CA', 'A0F482EA', 'A40EE1C3', 'BA1073EF', 'FB949DF5', '66AEA066', '39AA8F48'],
		'PUSBH0G' : ['A854C73E', '95C6A8C3', '22875B5A', '6B29E9B0', 'AC52E274', '3B321D00', '70EC31FD', '206EE24F'],
		'PUSBHA2' : ['21FA6690', '7D89A525', '27E06CF4', 'F7A32C75', 'EB2903AD', 'D2A93C37', '3797D024', '4EA743F7'],
		'PUSBHA3' : ['A423F04D', '43E267CA', 'E73FE235', 'B4688AF2', '4EFA5F66', '62805C0A', '92448CEF', 'D8974480'],
		'PUSCC01' : ['6B8B34E7', '114DA6DB', '90CE96B0', '80C25A92', '53B124E4', '345CE379', '8F0FF76D', '65120379'],
		'PUSCC0C' : ['5109E28E', '641B4766', '75AA4490', 'CEAE710C', 'AF1862A5', '9FC0303B', '73A6B12C', 'BD2266FC'],
		'PUSCC0G' : ['C7635B4E', '1EBBAC6F', 'F7D99D20', '0189797F', 'B95AF33E', '5F66B0CE', '65E420B7', 'A4E60BFB'],
		'PUSCCA2' : ['4ECDFAE0', 'F6F4A189', 'F2BEAA8E', '9D03BCBA', 'FE2112E7', 'B6FD91F9', '229FC16E', 'CA2FAA43'],
		'PUSCCA3' : ['CB146C3D', 'C89F6366', '3261244F', 'DEC81A3D', '5BF24E2C', '06D4F1C4', '874C9DA5', '5C1FAD34'],
		'PUSCCO01' : ['1783799F', '83415DA1', 'F4C7EDAE', '5A44A9A6', 'CE64662A', '435ED25A', '12DAB5A3', 'BE2186C0'],
		'PUSCCO0C' : ['2D01AFF6', 'F617BC1C', '11A33F8E', '14288238', '32CD206B', 'E8C20118', 'EE73F3E2', '6611E345'],
		'PUSCCO0G' : ['BB6B1636', '8CB75715', '93D0E63E', 'DB0F8A4B', '248FB1F0', '286481ED', 'F8316279', '7FD58E42'],
		'PUSCCOA2' : ['32C5B798', '64F85AF3', '96B7D190', '47854F8E', '63F45029', 'C1FFA0DA', 'BF4A83A0', '111C2FFA'],
		'PUSCCOA3' : ['B71C2145', '5A93981C', '56685F51', '044EE909', 'C6270CE2', '71D6C0E7', '1A99DF6B', '872C288D'],
		'PUSCL01' : ['F648BCB3', '60D232A9', 'A51BE697', '4E54C5D1', 'FFA3043D', 'DD2CAB8F', '231DD7B4', '58555F72'],
		'PUSCL0C' : ['CCCA6ADA', '1584D314', '407F34B7', '0038EE4F', '030A427C', '76B078CD', 'DFB491F5', '80653AF7'],
		'PUSCL0G' : ['5AA0D31A', '6F24381D', 'C20CED07', 'CF1FE63C', '1548D3E7', 'B616F838', 'C9F6006E', '99A157F0'],
		'PUSCL1A2' : ['4F5EB775', '43A46001', 'A1382935', 'D234E738', '46DA45B6', '877F6A70', '9A64963F', 'FD0F6EC4'],
		'PUSCL1A3' : ['CA8721A8', '7DCFA2EE', '61E7A7F4', '91FF41BF', 'E309197D', '37560A4D', '3FB7CAF4', '6B3F69B3'],
		'PUSCLT02' : ['52B1CF36', '47669010', '7A0C5532', 'D9CF1930', 'CCF49A52', '0BFE8BA1', '104A49DB', 'C32C9F11'],
		'PUSCLT0C' : ['A65FD3E2', '318B4646', '9E0E658B', '13F8A8FD', '9E2F4895', '7018F8A4', '42919B1C', 'A14DF30D'],
		'PUSCLT0G' : ['30356A22', '4B2BAD4F', '1C7DBC3B', 'DCDFA08E', '886DD90E', 'B0BE7851', '54D30A87', 'B8899E0A'],
		'PUSCPI3' : ['CBFF2A5B', '814126A7', 'D8DDE540', '71DB5F9A', 'F48A95ED', '38D0947E', '28344664', '7D8814E2'],
		'PUSCPI4' : ['93F95926', 'F85AFA45', '5BC8DE69', '3AA7CDBA', '4CBA90F0', '280CB4CC', '90044379', 'DE1D707C'],
		'PUSCPI5' : ['1620CFFB', 'C63138AA', '9B1750A8', '796C6B3D', 'E969CC3B', '9825D4F1', '35D71FB2', '482D770B'],
		'PUSCPIC' : ['BAC8A052', 'C9C7321E', 'FC005B38', 'F82748D0', '03821BE1', 'F31F8746', 'DF3CC868', '89D97F89'],
		'PUSCPIG' : ['2CA21992', 'B367D917', '7E738288', '370040A3', '15C08A7A', '33B907B3', 'C97E59F3', '901D128E'],
		'PUSCT01' : ['3E1B5738', '624926A3', '126EE279', 'C17226CB', '61895A92', '74FE9ADB', 'BD37891B', '90A76A60'],
		'PUSCT0C' : ['04998151', '171FC71E', 'F70A3059', '8F1E0D55', '9D201CD3', 'DF624999', '419ECF5A', '48970FE5'],
		'PUSCT0G' : ['92F33891', '6DBF2C17', '7579E9E9', '40390526', '8B628D48', '1FC4C96C', '57DC5EC1', '515362E2'],
		'PUSCT1A2' : ['9EFF83E0', 'F4D164EF', 'FB1AC260', '4549FA45', '2F3A5DA1', '195534DF', 'F3848E28', '8D70C351'],
		'PUSCT1A3' : ['1B26153D', 'CABAA600', '3BC54CA1', '06825CC2', '8AE9016A', 'A97C54E2', '5657D2E3', '1B40C426'],
		'PUSCT2A2' : ['E795FEF1', '0403FA98', '357608DD', 'ECCFACE6', 'CC3DD22F', '844FDCEE', '108301A6', 'D4CE8553'],
		'PUSCT2A3' : ['624C682C', '3A683877', 'F5A9861C', 'AF040A61', '69EE8EE4', '3466BCD3', 'B5505D6D', '42FE8224'],
		'PUSCV01' : ['AFAAD190', 'FDD71D4F', '59DBBE19', '307492BF', '1C8E7FD0', '5DEF054C', 'C030AC59', 'FE73EE63'],
		'PUSCV0C' : ['952807F9', '8881FCF2', 'BCBF6C39', '7E18B921', 'E0273991', 'F673D60E', '3C99EA18', '26438BE6'],
		'PUSCV0G' : ['0342BE39', 'F22117FB', '3ECCB589', 'B13FB152', 'F665A80A', '36D556FB', '2ADB7B83', '3F87E6E1'],
		'PUSCV1A2' : ['FDDA2367', 'BF64388F', '56DEAC81', 'C93F348F', 'A912AB8F', '6452119D', '75AC7806', '06B8CAFB'],
		'PUSCV1A3' : ['7803B5BA', '810FFA60', '96012240', '8AF49208', '0CC1F744', 'D47B71A0', 'D07F24CD', '9088CD8C'],
		'PUSGA01' : ['7D76839B', '18B924F7', 'C0F466C9', '282F03A8', '22E7EDFB', 'E743366A', 'FE593E72', '5C51E5F5'],
		'PUSGA0C' : ['47F455F2', '6DEFC54A', '2590B4E9', '66432836', 'DE4EABBA', '4CDFE528', '02F07833', '84618070'],
		'PUSGA0G' : ['D19EEC32', '174F2E43', 'A7E36D59', 'A9642045', 'C80C3A21', '8C7965DD', '14B2E9A8', '9DA5ED77'],
		'PUSGA1A2' : ['D93BF50F', '264BE05F', '992DAF08', 'C4364F9C', '6B9DE14E', '5A3B83B6', 'B72332C7', 'E07184C3'],
		'PUSGA1A3' : ['5CE263D2', '182022B0', '59F221C9', '87FDE91B', 'CE4EBD85', 'EA12E38B', '12F06E0C', '764183B4'],
		'PUSGAB1' : ['4D79E65D', 'FDDDF6D7', '53302619', 'D368F939', 'BC1FA74F', '1BEA702B', '60A174C6', '8A6E687D'],
		'PUSGAB2' : ['83152CE0', 'FE66C13C', '5256C480', '5733636A', '126D33C9', 'CB90D06C', 'CED3E040', '303F61E4'],
		'PUSGAB3' : ['06CCBA3D', 'C00D03D3', '92894A41', '14F8C5ED', 'B7BE6F02', '7BB9B051', '6B00BC8B', 'A60F6693'],
		'PUSGABC' : ['77FB3034', '888B176A', 'B654F439', '9D04D2A7', '40B6E10E', 'B076A369', '9C083287', '525E0DF8'],
		'PUSGABG' : ['E19189F4', 'F22BFC63', '34272D89', '5223DAD4', '56F47095', '70D0239C', '8A4AA31C', '4B9A60FF'],
		'PUSLR01' : ['F6A84794', 'B7396B6B', '3905938F', 'F309652A', '374F8C8B', 'E2D96A61', 'EBF15F02', '74CB843C'],
		'PUSLR0C' : ['CC2A91FD', 'C26F8AD6', 'DC6141AF', 'BD654EB4', 'CBE6CACA', '4945B923', '17581943', 'ACFBE1B9'],
		'PUSLR0G' : ['5A40283D', 'B8CF61DF', '5E12981F', '724246C7', 'DDA45B51', '89E339D6', '011A88D8', 'B53F8CBE'],
		'PUSLR1A2' : ['AFA59075', 'DFBA1519', 'D09288CC', 'BE5BCC8D', '28184C23', '4F93E2C6', 'F4A69FAA', '80B8F8F6'],
		'PUSLR1A3' : ['2A7C06A8', 'E1D1D7F6', '104D060D', 'FD906A0A', '8DCB10E8', 'FFBA82FB', '5175C361', '1688FF81'],
		'PUSM02C' : ['1CB5EAD0', 'E926288F', 'D53AA403', 'A1DF41ED', '31269621', '8C804F71', 'ED9845A8', 'E5A77540'],
		'PUSM02G' : ['8ADF5310', '9386C386', '57497DB3', '6EF8499E', '276407BA', '4C26CF84', 'FBDAD433', 'FC631847'],
		'PUSM03' : ['30692F0A', '7EE62EAD', 'F23AED6D', 'B21BBD53', '696AF758', '857CBBCC', 'B5D424D1', '39C3C1D2'],
		'PUSM04C' : ['AAFE2828', 'AAEC9D67', '359F99EC', '24633DE3', '0B134642', '916316A7', 'D7AD95CB', '63002F16'],
		'PUSM04G' : ['3C9491E8', 'D04C766E', 'B7EC405C', 'EB443590', '1D51D7D9', '51C59652', 'C1EF0450', '7AC44211'],
		'PUSM0C' : ['415EA503', '36603A14', 'D6E75315', '3BE7AA19', '9E627954', '4EB3A8F4', '42DCAADD', 'CD92AAB9'],
		'PUSM0G' : ['D7341CC3', '4CC0D11D', '54948AA5', 'F4C0A26A', '8820E8CF', '8E152801', '549E3B46', 'D456C7BE'],
		'PUSM2A2' : ['3F041AF7', '25EE99D4', '86052D91', '801FEC2A', '34095CB6', '870DB969', 'E8B78F3F', '7E1C0BCE'],
		'PUSM2A3' : ['BADD8C2A', '1B855B3B', '46DAA350', 'C3D44AAD', '91DA007D', '3724D954', '4D64D3F4', 'E82C0CB9'],
		'PUSM3A2' : ['D7DFE14E', '4AA23C4F', '03DCBB4C', 'D89F0EFD', 'AA09F67A', '3306CECF', '76B725F3', '4976C9CF'],
		'PUSM3A3' : ['52067793', '74C9FEA0', 'C303358D', '9B54A87A', '0FDAAAB1', '832FAEF2', 'D3647938', 'DF46CEB8'],
		'PUSM4A2' : ['CDD0E0D5', 'C54BA43B', '5BDAC831', '931430B7', 'B3003370', 'BD38690A', '6FBEE0F9', 'CC6086CA'],
		'PUSM4A3' : ['48097608', 'FB2066D4', '9B0546F0', 'D0DF9630', '16D36FBB', '0D110937', 'CA6DBC32', '5A5081BD'],
		'PUSMB01' : ['28A64D7E', 'CE0DE5BA', '95429BA6', 'BF09405C', '5F6A4CE0', 'B2451ECA', '83D49F69', '610F1E98'],
		'PUSMB02' : ['E6CA87C3', 'CDB6D251', '9424793F', '3B52DA0F', 'F118D866', '623FBE8D', '2DA60BEF', 'DB5E1701'],
		'PUSMB1G' : ['F2AF2D4A', '012461CF', '9D1935AD', 'DFF4315E', '018AEC9C', '7CAC11B6', 'DD343F15', 'E1CA0D03'],
		'PUSMB2G' : ['298A4C36', '00428356', '6DCBABDA', 'BD29B7B4', '9C9004AD', 'D2DE8530', '402ED724', '22992028'],
		'PUSMBG12' : ['2FAB799F', 'BBDFE59B', 'F4C7D586', '4C8368A5', '9122D2D0', '5D62A9E1', '4D9C0159', 'F9C90B49'],
		'PUSMBG13' : ['AA72EF42', '85B42774', '34185B47', '0F48CE22', '34F18E1B', 'ED4BC9DC', 'E84F5D92', '6FF90C3E'],
		'PUSMBG14' : ['F2749C3F', 'FCAFFB96', 'B70D606E', '44345C02', '8CC18B06', 'FD97E96E', '507F588F', 'CC6C68A0'],
		'PUSMBG15' : ['77AD0AE2', 'C2C43979', '77D2EEAF', '07FFFA85', '2912D7CD', '4DBE8953', 'F5AC0444', '5A5C6FD7'],
		'PUSMBG16' : ['B9C1C05F', 'C17F0E92', '76B40C36', '83A460D6', '8760434B', '9DC42914', '5BDE90C2', 'E00D664E'],
		'PUSMBG17' : ['3C185682', 'FF14CC7D', 'B66B82F7', 'C06FC651', '22B31F80', '2DED4929', 'FE0DCC09', '763D6139'],
		'PUSMBG18' : ['09CD26A5', '724FC78C', '709F7A64', '155C4497', 'F7014971', 'FC7A19AB', '2BBF9AF8', 'E720DEA9'],
		'PUSMBGP1' : ['66D105FE', '97A21467', '6A5AF1B4', '491E2DA3', 'F22E3AB4', '44C10D62', '2E90E93D', '07E66039'],
		'PUSMBS2G' : ['BAF0A339', '35222452', '2EA81C8C', 'C3787D0B', '999E8845', '95E85F04', '45205BCC', 'ED340862'],
		'PUSMBS2' : ['CC185FFE', '23C9781E', '94418478', '39FFD15F', '15773B13', 'A0477204', 'C9C9E89A', '1D4243DA'],
		'PUSMBSG2' : ['28D1AE8E', '5F1EF004', '54F42D21', '592510C5', 'CDC12668', '6A31EFA8', '117FF5E1', '8738C5BE'],
		'PUSMBSS1' : ['910E7A4C', '1512E8F1', 'D644D1B7', 'C3F581B3', 'BE0B237D', '370B0877', '62B5F0F4', '68BE6209'],
		'PUSMBSS2' : ['5F62B0F1', '16A9DF1A', 'D722332E', '47AE1BE0', '1079B7FB', 'E771A830', 'CCC76472', 'D2EF6B90'],
		'PUSMBSSG' : ['3DE615E5', '1AE4E245', 'B153DA27', '42BEA25E', '54E0F4A7', '5C315BC0', '885E272E', 'A94A6A8B'],
		'PUSMBSTG' : ['FD4CD880', '99F1D96C', '3EBA4253', '26B48CBF', 'DADE5362', 'E4015EDD', '066080EB', '6EDC2BC4'],
		'PUSMBST' : ['BA5637E3', 'C4BEDC8D', '38927946', 'C52DA3A5', '649E3ACA', '49EAC1D3', 'B820E943', 'B8A6FC45'],
		'PUSMC01' : ['C07DB6C7', 'A1414021', '109B0D7B', 'E789A28B', 'C16AE62C', '064E696C', '1DD435A5', '5665DC99'],
		'PUSMC02' : ['0E117C7A', 'A2FA77CA', '11FDEFE2', '63D238D8', '6F1872AA', 'D634C92B', 'B3A6A123', 'EC34D500'],
		'PUSMC04' : ['D3CE99DA', 'E58A69C7', '52375A0A', '6B650C7F', '72FB2B7C', '76C189A4', 'AE45F8F5', 'D991B6E9'],
		'PUSMC0C' : ['FAFF60AE', 'D417A19C', 'F5FFDF5B', 'A9E58915', '3DC3A06D', 'ADD2BA2E', 'E17D73E4', '8E55B91C'],
		'PUSMC0G' : ['6C95D96E', 'AEB74A95', '778C06EB', '66C28166', '2B8131F6', '6D743ADB', 'F73FE27F', '9791D41B'],
		'PUSMC1A2' : ['E3C179BA', 'F6248BED', '2294CE8E', '4348B797', '24253577', 'B9B68861', 'F89BE6FE', 'CAA13D23'],
		'PUSMC1A3' : ['6618EF67', 'C84F4902', 'E24B404F', '00831110', '81F669BC', '099FE85C', '5D48BA35', '5C913A54'],
		'PUSME01' : ['32A94CE5', '41E47DCE', 'CD44E8DB', 'F4827E16', '466389EA', '3C7BB90F', '9ADD5A63', 'E419519D'],
		'PUSME0C' : ['082B9A8C', '34B29C73', '28203AFB', 'BAEE5588', 'BACACFAB', '97E76A4D', '66741C22', '3C293418'],
		'PUSME0G' : ['9E41234C', '4E12777A', 'AA53E34B', '75C95DFB', 'AC885E30', '5741EAB8', '70368DB9', '25ED591F'],
		'PUSMEA2' : ['17EF82E2', 'A65D7A9C', 'AF34D4E5', 'E943983E', 'EBF3BFE9', 'BEDACB8F', '374D6C60', '4B24F8A7'],
		'PUSMEA3' : ['9236143F', '9836B873', '6FEB5A24', 'AA883EB9', '4E20E322', '0EF3ABB2', '929E30AB', 'DD14FFD0'],
		'PUSPK01' : ['80CD52E7', 'FBF167D4', '4A0446F0', 'EA3994D4', '52D48CA2', '9B2438B8', '8E6A5F2B', 'ACBBBC35'],
		'PUSPK0C' : ['BA4F848E', '8EA78669', 'AF6094D0', 'A455BF4A', 'AE7DCAE3', '30B8EBFA', '72C3196A', '748BD9B0'],
		'PUSPK0G' : ['2C253D4E', 'F4076D60', '2D134D60', '6B72B739', 'B83F5B78', 'F01E6B0F', '648188F1', '6D4FB4B7'],
		'PUSPKA2' : ['A58B9CE0', '1C486086', '28747ACE', 'F7F872FC', 'FF44BAA1', '19854A38', '23FA6928', '0386150F'],
		'PUSPKA3' : ['20520A3D', '2223A269', 'E8ABF40F', 'B433D47B', '5A97E66A', 'A9AC2A05', '862935E3', '95B61278'],
		'PUSRC01' : ['64247BAF', '4E3237B2', '8A132B4B', 'E352FB17', '61E79F5F', '816DF2C9', 'BD594CD6', '9F22A691'],
		'PUSRC0C' : ['5EA6ADC6', '3B64D60F', '6F77F96B', 'AD3ED089', '9D4ED91E', '2AF1218B', '41F00A97', '4712C314'],
		'PUSRC0G' : ['C8CC1406', '41C43D06', 'ED0420DB', '6219D8FA', '8B0C4885', 'EA57A17E', '57B29B0C', '5ED6AE13'],
		'PUSRCA2' : ['4162B5A8', 'A98B30E0', 'E8631775', 'FE931D3F', 'CC77A95C', '03CC8049', '10C97AD5', '301F0FAB'],
		'PUSRCA3' : ['C4BB2375', '97E0F20F', '28BC99B4', 'BD58BBB8', '69A4F597', 'B3E5E074', 'B51A261E', 'A62F08DC'],
		'PUSRI01' : ['725974C8', '2FDA0058', 'AC757471', '9749EE6A', 'A9FB5FCE', 'CF32826D', '75458C47', '49A7319C'],
		'PUSRI0C' : ['48DBA2A1', '5A8CE1E5', '4911A651', 'D925C5F4', '5552198F', '64AE512F', '89ECCA06', '91975419'],
		'PUSRI0G' : ['DEB11B61', '202C0AEC', 'CB627FE1', '1602CD87', '43108814', 'A408D1DA', '9FAE5B9D', '8853391E'],
		'PUSRIA2' : ['571FBACF', 'C863070A', 'CE05484F', '8A880842', '046B69CD', '4D93F0ED', 'D8D5BA44', 'E69A98A6'],
		'PUSRIA3' : ['D2C62C12', 'F608C5E5', '0EDAC68E', 'C943AEC5', 'A1B83506', 'FDBA90D0', '7D06E68F', '70AA9FD1'],
		'PUSRN01' : ['68567553', 'A033982C', 'F473070C', 'DCC2D020', 'B0F29AC4', '410C25A8', '6C4C494D', 'CCB17E99'],
		'PUSRN0C' : ['52D4A33A', 'D5657991', '1117D52C', '92AEFBBE', '4C5BDC85', 'EA90F6EA', '90E50F0C', '14811B1C'],
		'PUSRN0G' : ['C4BE1AFA', 'AFC59298', '93640C9C', '5D89F3CD', '5A194D1E', '2A36761F', '86A79E97', '0D45761B'],
		'PUSRNA2' : ['4D10BB54', '478A9F7E', '96033B32', 'C1033608', '1D62ACC7', 'C3AD5728', 'C1DC7F4E', '638CD7A3'],
		'PUSRNA3' : ['C8C92D89', '79E15D91', '56DCB5F3', '82C8908F', 'B8B1F00C', '73843715', '640F2385', 'F5BCD0D4'],
		'PUSSC01' : ['F5B51301', 'CBEBA16F', 'FCF224D6', 'A5699C72', '22F3E448', '1F6D5805', 'FE4D37C1', 'FA451A29'],
		'PUSSC0C' : ['CF37C568', 'BEBD40D2', '1996F6F6', 'EB05B7EC', 'DE5AA209', 'B4F18B47', '02E47180', '22757FAC'],
		'PUSSC0G' : ['595D7CA8', 'C41DABDB', '9BE52F46', '2422BF9F', 'C8183392', '74570BB2', '14A6E01B', '3BB112AB'],
		'PUSSCA3' : ['552A4BDB', '123964D2', '5E5D9629', 'FB63DCDD', '2AB08E80', '2DE54AB8', 'F60E5D09', 'C348B464'],
		'TASS01' : ['F53293AC', 'B5DE90B9', 'F29F4F61', 'BE230205', '6BBA92E2', '717B5D79', 'B704416B', '3B5F8624'],
		'TEUMPV01' : ['1B157170', 'D9C46F45', '9B4DB725', '414A8DED', 'E04D02E6', 'F7E58C32', '3CF3D16F', '788E201B'],
		'TUSAC01' : ['EAA3FC89', 'DDB4CB6F', 'F22DF022', '9F15C858', 'AAA2D4C9', 'CB281F8B', '761C0740', 'FDFE4527'],
		'TUSAC02' : ['24CF3634', 'DE0FFC84', 'F34B12BB', '1B4E520B', '04D0404F', '1B52BFCC', 'D86E93C6', '47AF4CBE'],
		'TUSB01' : ['E0C85335', '51CC3351', '811AC0C6', 'BB8EBF98', '4CAAC67C', '76FFD849', '901415F5', '3EA702AC'],
		'TUSB02' : ['2EA49988', '527704BA', '807C225F', '3FD525CB', 'E2D852FA', 'A685780E', '3E668173', '84F60B35'],
		'TUSCC01' : ['89865C0E', '9601970F', '5FE99EC3', '13630692', '2C8A22E7', 'B62F3AC9', 'F034F16E', '76364C8D'],
		'TUSDTT01' : ['5FEB4E70', 'FC256603', '3D90F56E', 'CDF17F1E', 'E41773E1', 'F3F8122E', '38A9A068', 'E3D0512B'],
		'TUSDTT1B' : ['96510159', '77C7CB90', '77670C14', '21E0A0E8', '09661ECD', '4D9EFD9A', 'D5D8CD44', 'ECE128C0'],
		'TUSGSV' : ['B233F2FB', '76D85CFA', 'FEC06163', 'BCB7EA8B', '18F19853', '4A2CFF78', 'C44F4BDA', '20AD2599'],
		'TUSLM01' : ['C6F9C56D', 'BD07D6C1', '1951EC6F', 'A405E47A', 'CF57112D', '47462540', '13E9C2A4', '2A0BB1DF'],
		'TUSLT01' : ['E671D55F', 'D0D06750', '2BFD7E5C', '73A3E5B7', 'CF7DE54E', '5A9F63B2', '13C336C7', 'D59346CC'],
		'TUSLT02' : ['281D1FE2', 'D36B50BB', '2A9B9CC5', 'F7F87FE4', '610F71C8', '8AE5C3F5', 'BDB1A241', '6FC24F55'],
		'TUSLT03' : ['ADC4893F', 'ED009254', 'EA441204', 'B433D963', 'C4DC2D03', '3ACCA3C8', '1862FE8A', 'F9F24822'],
		'TUSLT04' : ['F5C2FA42', '941B4EB6', '6951292D', 'FF4F4B43', '7CEC281E', '2A10837A', 'A052FB97', '5A672CBC'],
		'TUSLT07' : ['3BAE30FF', '97A0795D', '6837CBB4', '7B14D110', 'D29EBC98', 'FA6A233D', '0E206F11', 'E0362525'],
		'TUSLT08' : ['0E7B40D8', '1AFB72AC', 'AEC33327', 'AE2753D6', '072CEA69', '2BFD73BF', 'DB9239E0', '712B9AB5'],
		'TUSLT09' : ['8BA2D605', '2490B043', '6E1CBDE6', 'EDECF551', 'A2FFB6A2', '9BD41382', '7E41652B', 'E71B9DC2'],
		'TUSPK01B' : ['9EA81215', '608BC74F', 'FCEE0097', 'B8CC8489', '2C06F53D', 'DDFF0E7E', 'F0B826B4', '7BB2A12A'],
		'TUSPK01' : ['62C03A0E', '7CBD5600', '85234E83', '7998C8D4', '2DEF8AA1', '1957E108', 'F1515928', 'BF9FF3C1'],
		'TUSRV01' : ['4208F631', '25E4BDF2', '8C210B91', 'C0456F3A', '51E3C268', '6AADCD4C', '8D5D11E1', '1767047F'],
		'TUSRV02' : ['8C643C8C', '265F8A19', '8D47E908', '441EF569', 'FF9156EE', 'BAD76D0B', '232F8567', 'AD360DE6'],
		'TUSSL01' : ['8A7BF3BC', '3D3804C9', '06005C82', 'F85E5F31', 'F1DAC292', '746EC943', '2D64111B', 'D42609D6'],
		'TUSSMT01' : ['293ED17C', '621F8B33', '44C37279', 'A8230624', '5F796224', '4BFD4785', '83C7B1AD', '648380D4'],
		'TUSSMT02' : ['E7521BC1', '61A4BCD8', '45A590E0', '2C789C77', 'F10BF6A2', '9B87E7C2', '2DB5252B', 'DED2894D'],
		'TUSSMT03' : ['628B8D1C', '5FCF7E37', '857A1E21', '6FB33AF0', '54D8AA69', '2BAE87FF', '886679E0', '48E28E3A'],
		'TUSSMT04' : ['3A8DFE61', '26D4A2D5', '066F2508', '24CFA8D0', 'ECE8AF74', '3B72A74D', '30567CFD', 'EB77EAA4'],
		'TUSSUV01' : ['692E6341', '4AF4B431', '5554C54C', 'CE58AF2D', '4B9E5F71', 'FCC686BD', '97208CF8', '7A28A942'],
		'TUSSUV02' : ['A742A9FC', '494F83DA', '543227D5', '4A03357E', 'E5ECCBF7', '2CBC26FA', '3952187E', 'C079A0DB'],
		'TUSSV01' : ['D3999E9F', 'A03D2B2F', 'FAC0040C', '867E085F', '12F7B97F', 'F4AD6780', 'CE496AF6', '7200B8C7'],
		'TUSSV' : ['8716EF8D', 'B1F5E042', 'C02BD966', '31839334', '962447F1', '69D05BC0', '4A9A9478', '89C9527D'],
		'TUSSW01' : ['3B426526', 'CF718EB4', '7F1992D1', 'DEFEEA88', '8CF713B3', '40A61026', '5049C03A', '456A7AC6'],
		'TUSTR01' : ['C5041BE8', '87005E51', 'AC0070A9', 'F7D52457', '2194929F', 'FE80ED7E', 'FD2A4116', '1790665D'],
		'TUSTR02' : ['0B68D155', '84BB69BA', 'AD669230', '738EBE04', '8FE60619', '2EFA4D39', '5358D590', 'ADC16FC4'],
		'TUSTR03' : ['8EB14788', 'BAD0AB55', '6DB91CF1', '30451883', '2A355AD2', '9ED32D04', 'F68B895B', '3BF168B3'],
		'TUSTR04' : ['D6B734F5', 'C3CB77B7', 'EEAC27D8', '7B398AA3', '92055FCF', '8E0F0DB6', '4EBB8C46', '98640C2D'],
		'TUSTR05' : ['536EA228', 'FDA0B558', '2E73A919', '38F22C24', '37D60304', '3E266D8B', 'EB68D08D', '0E540B5A'],
		'TUSTR06' : ['9D026895', 'FE1B82B3', '2F154B80', 'BCA9B677', '99A49782', 'EE5CCDCC', '451A440B', 'B40502C3'],
		'TUSV01B' : ['83518924', '287EF77E', 'AB1736EF', '4E588952', 'DA08B1F6', '6D85B35B', '06B6627F', '3D30086F'],
		'TUSV01' : ['CC324DFB', 'D21A2D5E', 'CDD67EB2', '53B89562', '9D953784', 'AB4749DA', '412BE40D', '92AC2DB7'],
		'TUSV02B' : ['5874E858', '291815E7', '5BC5A898', '2C850FB8', '471259C7', 'C3F727DD', '9BAC8A4E', 'FE632544'],
		'TUSV02' : ['025E8746', 'D1A11AB5', 'CCB09C2B', 'D7E30F31', '33E7A302', '7B3DE99D', 'EF59708B', '28FD242E'],
		'XASBCB1' : ['518393A3', '1295EF9B', 'F2D6DF29', '5A242893', '399C365F', '81358960', 'E522E5D6', '3C449AE2'],
		'XASBCB2' : ['9FEF591E', '112ED870', 'F3B03DB0', 'DE7FB2C0', '97EEA2D9', '514F2927', '4B507150', '8615937B'],
		'XASBCB3' : ['1A36CFC3', '2F451A9F', '336FB371', '9DB41447', '323DFE12', 'E166491A', 'EE832D9B', '1025940C'],
		'XASBCBC' : ['6B0145CA', '67C30E26', '17B20D09', '1448030D', 'C535701E', '2AA95A22', '198BA397', 'E474FF67'],
		'XASBCBG' : ['FD6BFC0A', '1D63E52F', '95C1D4B9', 'DB6F0B7E', 'D377E185', 'EA0FDAD7', '0FC9320C', 'FDB09260'],
		'XASBS1B2' : ['29094C81', '5C6DFC42', '9DA962B8', '4BAAC102', 'AB230B4E', '5AFB3D5C', '779DD8C7', '2F912D9A'],
		'XASBS1B3' : ['ACD0DA5C', '62063EAD', '5D76EC79', '08616785', '0EF05785', 'EAD25D61', 'D24E840C', 'B9A12AED'],
		'XASBSB1' : ['1E1CF1E7', 'EE78F797', '2870D89D', '501F6A80', '12AD8D23', '4FA95707', 'CE135EAA', '4CE7BCFE'],
		'XASBSBC' : ['249E278E', '9B2E162A', 'CD140ABD', '1E73411E', 'EE04CB62', 'E4358445', '32BA18EB', '94D7D97B'],
		'XASBSBG' : ['B2F49E4E', 'E18EFD23', '4F67D30D', 'D154496D', 'F8465AF9', '249304B0', '24F88970', '8D13B47C'],
		'XASBSCB1' : ['4430991A', 'CC128B79', 'A64D5648', '1C20A57B', 'BEA59CDF', '1479D7AF', '621B4F56', '4B3A1C6C'],
		'XASBSCB2' : ['8A5C53A7', 'CFA9BC92', 'A72BB4D1', '987B3F28', '10D70859', 'C40377E8', 'CC69DBD0', 'F16B15F5'],
		'XASBSCB3' : ['0F85C57A', 'F1C27E7D', '67F43A10', 'DBB099AF', 'B5045492', '742A17D5', '69BA871B', '675B1282'],
		'XASBSCBC' : ['7EB24F73', 'B9446AC4', '43298468', '524C8EE5', '420CDA9E', 'BFE504ED', '9EB20917', '930A79E9'],
		'XASBSCBG' : ['E8D8F6B3', 'C3E481CD', 'C15A5DD8', '9D6B8696', '544E4B05', '7F438418', '88F0988C', '8ACE14EE'],
		'XASC1B1' : ['6347E42B', '04883996', 'BEB506DD', 'CFCEB1DC', 'C17C4E5F', '81CD6918', '1DC29DD6', '87D91E35'],
		'XASC1B2' : ['AD2B2E96', '07330E7D', 'BFD3E444', '4B952B8F', '6F0EDAD9', '51B7C95F', 'B3B00950', '3D8817AC'],
		'XASC1B3' : ['28F2B84B', '3958CC92', '7F0C6A85', '085E8D08', 'CADD8612', 'E19EA962', '1663559B', 'ABB810DB'],
		'XASC1BC' : ['59C53242', '71DED82B', '5BD1D4FD', '81A29A42', '3DD5081E', '2A51BA5A', 'E16BDB97', '5FE97BB0'],
		'XASC1BG' : ['CFAF8B82', '0B7E3322', 'D9A20D4D', '4E859231', '2B979985', 'EAF73AAF', 'F7294A0C', '462D16B7'],
		'XEUBRB2' : ['36CB5C4F', '57A1DB95', 'D957672F', '4A528EAE', 'E7DC74D4', 'DB01719C', '3B62A75D', '776BA672'],
		'XEUBRB3' : ['B312CA92', '69CA197A', '1988E9EE', '09992829', '420F281F', '6B2811A1', '9EB1FB96', 'E15BA105'],
		'XEUBRB' : ['9029FD79', '611B960E', 'FA8F46E0', '6C084E14', 'E0DEE67B', '724A6804', '3C6035F2', 'D28266AE'],
		'XEUBRC' : ['15F06BA4', '5F7054E1', '3A50C821', '2FC3E893', '450DBAB0', 'C2630839', '99B36939', '44B261D9'],
		'XEUBRG' : ['839AD264', '25D0BFE8', 'B8231191', 'E0E4E0E0', '534F2B2B', '02C588CC', '8FF1F8A2', '5D760CDE'],
		'XEUGT1BG' : ['D528AA7B', '10D0DA12', '9B8258C7', 'EB60B2A2', '5EEDB37B', '72F45B51', '825360F2', '93440DF6'],
		'XEULM1B1' : ['23E4135C', 'C0B17ADA', '2EF04341', '2EE60709', '6909E759', 'C47AA907', 'B5B734D0', '5699C42E'],
		'XEULM1BC' : ['1966C535', 'B5E79B67', 'CB949161', '608A2C97', '95A0A118', '6FE67A45', '491E7291', '8EA9A1AB'],
		'XEULM1BG' : ['8F0C7CF5', 'CF47706E', '49E748D1', 'AFAD24E4', '83E23083', 'AF40FAB0', '5F5CE30A', '976DCCAC'],
		'XEULMB2' : ['4F61347F', '6ADFB111', 'B6718B77', 'E9B4ABE7', 'F2242DB9', 'CEFF6D18', '2E9AFE30', '09F80385'],
		'XEULMB3' : ['CAB8A2A2', '54B473FE', '76AE05B6', 'AA7F0D60', '57F77172', '7ED60D25', '8B49A2FB', '9FC804F2'],
		'XEUR3B2' : ['3D557BDA', '12FC1A8A', '9B23CE29', '1F95A2D4', 'E55C839D', '3D4EB602', '39E25014', '1FDBE753'],
		'XEUR3B3' : ['B88CED07', '2C97D865', '5BFC40E8', '5C5E0453', '408FDF56', '8D67D63F', '9C310CDF', '89EBE024'],
		'XEURC3B1' : ['F2C26282', '034A8E61', 'DF979543', 'E4B560FC', 'DD6467EA', '3CE0BEE1', '01DAB463', 'E8134F12'],
		'XEURC3BC' : ['C840B4EB', '761C6FDC', '3AF34763', 'AAD94B62', '21CD21AB', '977C6DA3', 'FD73F222', '30232A97'],
		'XEURC3BG' : ['5E2A0D2B', '0CBC84D5', 'B8809ED3', '65FE4311', '378FB030', '57DAED56', 'EB3163B9', '29E74790'],
		'XEURG1BC' : ['DEBD0397', '7FE8EDF0', '6AC9B71A', '02341258', '509BE8B4', '4463B8B0', '8C253B3D', '0960CC1B'],
		'XEURG1BG' : ['48D7BA57', '054806F9', 'E8BA6EAA', 'CD131A2B', '46D9792F', '84C53845', '9A67AAA6', '10A4A11C'],
		'XEURRB1' : ['6699B114', '8EBCEBCA', 'B40D37D0', 'EBA2D21D', '38EC20FE', '204A6AA7', 'E452F377', '526DB6BB'],
		'XEURRB2' : ['A8F57BA9', '8D07DC21', 'B56BD549', '6FF9484E', '969EB478', 'F030CAE0', '4A2067F1', 'E83CBF22'],
		'XEURRB3' : ['2D2CED74', 'B36C1ECE', '75B45B88', '2C32EEC9', '334DE8B3', '4019AADD', 'EFF33B3A', '7E0CB855'],
		'XEURRBC' : ['5C1B677D', 'FBEA0A77', '5169E5F0', 'A5CEF983', 'C44566BF', '8BD6B9E5', '18FBB536', '8A5DD33E'],
		'XEURRBG' : ['CA71DEBD', '814AE17E', 'D31A3C40', '6AE9F1F0', 'D207F724', '4B703910', '0EB924AD', '9399BE39'],
		'XEUSB1' : ['E40A9656', '7243FE65', '7CA69364', '2B48C0E7', 'C2093326', '886AA4B9', '1EB7E0AF', '8A59220B'],
		'XEUSB2' : ['2A665CEB', '71F8C98E', '7DC071FD', 'AF135AB4', '6C7BA7A0', '581004FE', 'B0C57429', '30082B92'],
		'XEUSB3' : ['AFBFCA36', '4F930B61', 'BD1FFF3C', 'ECD8FC33', 'C9A8FB6B', 'E83964C3', '151628E2', 'A6382CE5'],
		'XEUSBC' : ['DE88403F', '07151FD8', '99C24144', '6524EB79', '3EA07567', '23F677FB', 'E21EA6EE', '5269478E'],
		'XEUSBG' : ['48E2F9FF', '7DB5F4D1', '1BB198F4', 'AA03E30A', '28E2E4FC', 'E350F70E', 'F45C3775', '4BAD2A89'],
		'XEUSC2B2' : ['97BEF501', '195C138C', 'B3F31ABE', 'A6EDC2E7', 'D37D9B4F', '1B851217', '0FC348C6', 'D501E4B7'],
		'XEUSC2B3' : ['126763DC', '2737D163', '732C947F', 'E5266460', '76AEC784', 'ABAC722A', 'AA10140D', '4331E3C0'],
		'XEUSC2B' : ['72DC0BD4', 'F7245DAA', 'B4728EF9', '8AA9B631', '205A85F0', '286054D9', 'FCE45679', '6A9E3756'],
		'XEUSC2C' : ['F7059D09', 'C94F9F45', '74AD0038', 'C96210B6', '8589D93B', '984934E4', '59370AB2', 'FCAE3021'],
		'XEUSC2G' : ['616F24C9', 'B3EF744C', 'F6DED988', '064518C5', '93CB48A0', '58EFB411', '4F759B29', 'E56A5D26'],
		'XEUSC3B1' : ['B109C405', '75AB81FC', '374C6EFA', '7A36BA63', 'E30FA505', '7FF4C5F6', '3FB1768C', '583A2F2F'],
		'XEUSC3B2' : ['7F650EB8', '7610B617', '362A8C63', 'FE6D2030', '4D7D3183', 'AF8E65B1', '91C3E20A', 'E26B26B6'],
		'XEUSC3B3' : ['FABC9865', '487B74F8', 'F6F502A2', 'BDA686B7', 'E8AE6D48', '1FA7058C', '3410BEC1', '745B21C1'],
		'XEUSC3BC' : ['8B8B126C', '00FD6041', 'D228BCDA', '345A91FD', '1FA6E344', 'D46816B4', 'C31830CD', '800A4AAA'],
		'XEUSC3BG' : ['1DE1ABAC', '7A5D8B48', '505B656A', 'FB7D998E', '09E472DF', '14CE9641', 'D55AA156', '99CE27AD'],
		'XEUSRB1' : ['F708D9BA', '0B657D17', 'C2EC384D', 'AD99B578', '7BF85BE9', 'BE4AC06B', 'A7468860', '370A0A03'],
		'XEUSRB2' : ['39641307', '08DE4AFC', 'C38ADAD4', '29C22F2B', 'D58ACF6F', '6E30602C', '09341CE6', '8D5B039A'],
		'XEUSRB3' : ['BCBD85DA', '36B58813', '03555415', '6A0989AC', '705993A4', 'DE190011', 'ACE7402D', '1B6B04ED'],
		'XEUSRBC' : ['CD8A0FD3', '7E339CAA', '2788EA6D', 'E3F59EE6', '87511DA8', '15D61329', '5BEFCE21', 'EF3A6F86'],
		'XEUSRBG' : ['5BE0B613', '049377A3', 'A5FB33DD', '2CD29695', '91138C33', 'D57093DC', '4DAD5FBA', 'F6FE0281'],
		'XEUSVB1' : ['946DA530', '745E7B14', '5486818D', '4F94DD91', '81F6116D', 'AD6E8F9F', '5D48C2E4', 'EBA20304'],
		'XEUSVB2' : ['5A016F8D', '77E54CFF', '55E06314', 'CBCF47C2', '2F8485EB', '7D142FD8', 'F33A5662', '51F30A9D'],
		'XEUSVB3' : ['DFD8F950', '498E8E10', '953FEDD5', '8804E145', '8A57D920', 'CD3D4FE5', '56E90AA9', 'C7C30DEA'],
		'XEUSVBC' : ['AEEF7359', '01089AA9', 'B1E253AD', '01F8F60F', '7D5F572C', '06F25CDD', 'A1E184A5', '33926681'],
		'XEUSVBG' : ['3885CA99', '7BA871A0', '33918A1D', 'CEDFFE7C', '6B1DC6B7', 'C654DC28', 'B7A3153E', '2A560B86'],
		'XUSBCB1' : ['4F089886', '3E6FF155', 'EBA4C91B', '1BFD7E66', '702B1941', '1314CC4E', 'AC95CAC8', 'B104DD7A'],
		'XUSBCB2' : ['8164523B', '3DD4C6BE', 'EAC22B82', '9FA6E435', 'DE598DC7', 'C36E6C09', '02E75E4E', '0B55D4E3'],
		'XUSBCB3' : ['04BDC4E6', '03BF0451', '2A1DA543', 'DC6D42B2', '7B8AD10C', '73470C34', 'A7340285', '9D65D394'],
		'XUSBCBC' : ['758A4EEF', '4B3910E8', '0EC01B3B', '559155F8', '8C825F00', 'B8881F0C', '503C8C89', '6934B8FF'],
		'XUSBCBG' : ['E3E0F72F', '3199FBE1', '8CB3C28B', '9AB65D8B', '9AC0CE9B', '782E9FF9', '467E1D12', '70F0D5F8'],
		'XUSBHB1' : ['B1AE6C58', '30CB6324', '481B00FC', '376689CC', '2637731C', 'E940CB4C', 'FA89A095', '50EB8876'],
		'XUSBHB2' : ['7FC2A6E5', '337054CF', '497DE265', 'B33D139F', '8845E79A', '393A6B0B', '54FB3413', 'EABA81EF'],
		'XUSBHB3' : ['FA1B3038', '0D1B9620', '89A26CA4', 'F0F6B518', '2D96BB51', '89130B36', 'F12868D8', '7C8A8698'],
		'XUSBHBC' : ['8B2CBA31', '459D8299', 'AD7FD2DC', '790AA252', 'DA9E355D', '42DC180E', '0620E6D4', '88DBEDF3'],
		'XUSBHBG' : ['1D4603F1', '3F3D6990', '2F0C0B6C', 'B62DAA21', 'CCDCA4C6', '827A98FB', '1062774F', '911F80F4'],
		'XUSCCB1' : ['DE99F028', 'BBB66788', '9D45C686', '5DC61903', '333F6256', '8D146682', 'EF81B1DF', 'D46361C2'],
		'XUSCCB2' : ['10F53A95', 'B80D5063', '9C23241F', 'D99D8350', '9D4DF6D0', '5D6EC6C5', '41F32559', '6E32685B'],
		'XUSCCB3' : ['952CAC48', '8666928C', '5CFCAADE', '9A5625D7', '389EAA1B', 'ED47A6F8', 'E4207992', 'F8026F2C'],
		'XUSCCBC' : ['E41B2641', 'CEE08635', '782114A6', '13AA329D', 'CF962417', '2688B5C0', '1328F79E', '0C530447'],
		'XUSCCBG' : ['72719F81', 'B4406D3C', 'FA52CD16', 'DC8D3AEE', 'D9D4B58C', 'E62E3535', '056A6605', '15976940'],
		'XUSCCOB1' : ['955AC7C4', 'F86A9F67', '6BADFC69', '1F3F5EE5', '3D4F2FC4', '4181981D', 'E1F1FC4D', 'DD05EE9B'],
		'XUSCCOB2' : ['5B360D79', 'FBD1A88C', '6ACB1EF0', '9B64C4B6', '933DBB42', '91FB385A', '4F8368CB', '6754E702'],
		'XUSCCOB3' : ['DEEF9BA4', 'C5BA6A63', 'AA149031', 'D8AF6231', '36EEE789', '21D25867', 'EA503400', 'F164E075'],
		'XUSCCOBC' : ['AFD811AD', '8D3C7EDA', '8EC92E49', '5153757B', 'C1E66985', 'EA1D4B5F', '1D58BA0C', '05358B1E'],
		'XUSCCOBG' : ['39B2A86D', 'F79C95D3', '0CBAF7F9', '9E747D08', 'D7A4F81E', '2ABBCBAA', '0B1A2B97', '1CF1E619'],
		'XUSCL1B1' : ['E8C1C729', 'DF36A595', '5C2204CC', '8A8EF653', '18613A5B', '070152B7', 'C4DFE9D2', '3116AFA5'],
		'XUSCL1BC' : ['D2431140', 'AA604428', 'B946D6EC', 'C4E2DDCD', 'E4C87C1A', 'AC9D81F5', '3876AF93', 'E926CA20'],
		'XUSCL1BG' : ['4429A880', 'D0C0AF21', '3B350F5C', '0BC5D5BE', 'F28AED81', '6C3B0100', '2E343E08', 'F0E2A727'],
		'XUSCT01B' : ['280E22EA', '69897B53', '5AEAC0EE', '52252C9E', '9C08AF18', '6FEFD24B', '40B67C91', 'AF0D3452'],
		'XUSCT01C' : ['ADD7B437', '57E2B9BC', '9A354E2F', '11EE8A19', '39DBF3D3', 'DFC6B276', 'E565205A', '393D3325'],
		'XUSCT01G' : ['3BBD0DF7', '2D4252B5', '1846979F', 'DEC9826A', '2F996248', '1F603283', 'F327B1C1', '20F95E22'],
		'XUSCT1B2' : ['F70C3901', '6BF89690', '07660D00', '99A8717D', 'DFF3B6CA', '4951AC5F', '034D6543', 'FB380BA9'],
		'XUSCT1B3' : ['72D5AFDC', '5593547F', 'C7B983C1', 'DA63D7FA', '7A20EA01', 'F978CC62', 'A69E3988', '6D080CDE'],
		'XUSCT2A2' : ['5543256C', '9A4CEA7E', '39D859CA', '52F3A134', 'A1EED175', '7A39D0E8', '7D5002FC', '61D56080'],
		'XUSCT2A3' : ['D09AB3B1', 'A4272891', 'F907D70B', '113807B3', '043D8DBE', 'CA10B0D5', 'D8835E37', 'F7E567F7'],
		'XUSCV1B1' : ['5A45533B', '23F6FD1B', 'ABC48178', '918525E4', 'F7A9D462', 'E42C295A', '2B1707EB', 'CAA10B9A'],
		'XUSCV1B2' : ['94299986', '204DCAF0', 'AAA263E1', '15DEBFB7', '59DB40E4', '3456891D', '8565936D', '70F00203'],
		'XUSCV1B3' : ['11F00F5B', '1E26081F', '6A7DED20', '56151930', 'FC081C2F', '847FE920', '20B6CFA6', 'E6C00574'],
		'XUSCV1BC' : ['60C78552', '56A01CA6', '4EA05358', 'DFE90E7A', '0B009223', '4FB0FA18', 'D7BE41AA', '12916E1F'],
		'XUSCV1BG' : ['F6AD3C92', '2C00F7AF', 'CCD38AE8', '10CE0609', '1D4203B8', '8F167AED', 'C1FCD031', '0B550318'],
		'XUSLRB1' : ['43BA835B', '1DC2AA38', '348EC3B9', '2E0D26BB', '57C1CA39', '5B91EF9A', '8B7F19B0', 'C5BAE687'],
		'XUSLRB2' : ['8DD649E6', '1E799DD3', '35E82120', 'AA56BCE8', 'F9B35EBF', '8BEB4FDD', '250D8D36', '7FEBEF1E'],
		'XUSLRB3' : ['080FDF3B', '20125F3C', 'F537AFE1', 'E99D1A6F', '5C600274', '3BC22FE0', '80DED1FD', 'E9DBE869'],
		'XUSLRBC' : ['79385532', '68944B85', 'D1EA1199', '60610D25', 'AB688C78', 'F00D3CD8', '77D65FF1', '1D8A8302'],
		'XUSLRBG' : ['EF52ECF2', '1234A08C', '5399C829', 'AF460556', 'BD2A1DE3', '30ABBC2D', '6194CE6A', '044EEE05'],
		'XUSLT2B1' : ['95390C6B', '6E25AB5A', '55AFAD70', '9AFAA8C1', '1FDDA633', 'D5FE5DF6', 'C36375BA', 'C94014B0'],
		'XUSLT2BC' : ['AFBBDA02', '1B734AE7', 'B0CB7F50', 'D496835F', 'E374E072', '7E628EB4', '3FCA33FB', '11707135'],
		'XUSLT2BG' : ['39D163C2', '61D3A1EE', '32B8A6E0', '1BB18B2C', 'F53671E9', 'BEC40E41', '2988A260', '08B41C32'],
		'XUSM1B1' : ['D63A6D2E', '987EC1A2', '27928B24', 'E95C1F30', '1A10A389', '21FEA623', 'C6AE7000', '39EE864D'],
		'XUSM1B2' : ['1856A793', '9BC5F649', '26F469BD', '6D078563', 'B462370F', 'F1840664', '68DCE486', '83BF8FD4'],
		'XUSM1B3' : ['9D8F314E', 'A5AE34A6', 'E62BE77C', '2ECC23E4', '11B16BC4', '41AD6659', 'CD0FB84D', '158F88A3'],
		'XUSM1BC' : ['ECB8BB47', 'ED28201F', 'C2F65904', 'A73034AE', 'E6B9E5C8', '8A627561', '3A073641', 'E1DEE3C8'],
		'XUSM1BG' : ['7AD20287', '9788CB16', '408580B4', '68173CDD', 'F0FB7453', '4AC4F594', '2C45A7DA', 'F81A8ECF'],
		'XUSM2B1' : ['AF50103F', '68AC5FD5', 'E9FE4199', '40DA4993', 'F9172C07', 'BCE44E12', '25A9FF8E', '6050C04F'],
		'XUSM2B2' : ['613CDA82', '6B17683E', 'E898A300', 'C481D3C0', '5765B881', '6C9EEE55', '8BDB6B08', 'DA01C9D6'],
		'XUSM2B3' : ['E4E54C5F', '557CAAD1', '28472DC1', '874A7547', 'F2B6E44A', 'DCB78E68', '2E0837C3', '4C31CEA1'],
		'XUSM2BC' : ['95D2C656', '1DFABE68', '0C9A93B9', '0EB6620D', '05BE6A46', '17789D50', 'D900B9CF', 'B860A5CA'],
		'XUSM2BG' : ['03B87F96', '675A5561', '8EE94A09', 'C1916A7E', '13FCFBDD', 'D7DE1DA5', 'CF422854', 'A1A4C8CD'],
		'XUSM3B2X' : ['B548A7AC', 'A9F83021', '9B63D675', 'F2655A7C', '3A993338', '1AFAC6B8', 'E627E0B1', '2D83B052'],
		'XUSM3B3X' : ['C3A9A831', '6927BEE0', 'F42F73EE', '13D30893', '8E92449E', 'BF299A73', '522C9717', '6CB2AB4B'],
		'XUSM3C' : ['96D59568', 'B0CA5142', '69AADE11', '591C6F4A', '469952DF', '1481EB61', '9A278156', '6343D47E'],
		'XUSM3G' : ['00BF2CA8', 'CA6ABA4B', 'EBD907A1', '963B6739', '50DBC344', 'D4276B94', '8C6510CD', '7A87B979'],
		'XUSM4B1' : ['5D84EA1D', '8809623A', '3421A439', '53D1950E', '7E1E43C1', '86D19E71', 'A2A09048', 'D22C4D4B'],
		'XUSM4B2' : ['93E820A0', '8BB255D1', '354746A0', 'D78A0F5D', 'D06CD747', '56AB3E36', '0CD204CE', '687D44D2'],
		'XUSM4B3' : ['1631B67D', 'B5D9973E', 'F598C861', '9441A9DA', '75BF8B8C', 'E6825E0B', 'A9015805', 'FE4D43A5'],
		'XUSM4BC' : ['67063C74', 'FD5F8387', 'D1457619', '1DBDBE90', '82B70580', '2D4D4D33', '5E09D609', '0A1C28CE'],
		'XUSM4BG' : ['F16C85B4', '87FF688E', '5336AFA9', 'D29AB6E3', '94F5941B', 'EDEBCDC6', '484B4792', '13D845C9'],
		'XUSMEB1' : ['87BB882A', 'EB1FBC9D', 'C0CFB8ED', '29863D87', '26EDCF58', '85333CF4', 'FA531CD1', '55683326'],
		'XUSMEB2' : ['49D74297', 'E8A48B76', 'C1A95A74', 'ADDDA7D4', '889F5BDE', '55499CB3', '54218857', 'EF393ABF'],
		'XUSMEB3' : ['CC0ED44A', 'D6CF4999', '0176D4B5', 'EE160153', '2D4C0715', 'E560FC8E', 'F1F2D49C', '79093DC8'],
		'XUSMEBC' : ['BD395E43', '9E495D20', '25AB6ACD', '67EA1619', 'DA448919', '2EAFEFB6', '06FA5A90', '8D5856A3'],
		'XUSMEBG' : ['2B53E783', 'E4E9B629', 'A7D8B37D', 'A8CD1E6A', 'CC061882', 'EE096F43', '10B8CB0B', '949C3BA4'],
		'XUSMU3B' : ['9C55AE60', 'B8CDB77A', '5CC43D1F', 'B7808EF6', '5744CC2B', '02C1832B', '8BFA1FA2', '7EA7D76B'],
		'XUSPKB1' : ['35DF9628', '510AA687', '478F16C6', '373DD745', '325ACA10', '226CBD43', 'EEE41999', '1DCADE8E'],
		'XUSPKB2' : ['FBB35C95', '52B1916C', '46E9F45F', 'B3664D16', '9C285E96', 'F2161D04', '40968D1F', 'A79BD717'],
		'XUSPKB3' : ['7E6ACA48', '6CDA5383', '86367A9E', 'F0ADEB91', '39FB025D', '423F7D39', 'E545D1D4', '31ABD060'],
		'XUSPKBC' : ['0F5D4041', '245C473A', 'A2EBC4E6', '7951FCDB', 'CEF38C51', '89F06E01', '124D5FD8', 'C5FABB0B'],
		'XUSPKBG' : ['9937F981', '5EFCAC33', '20981D56', 'B676F4A8', 'D8B11DCA', '4956EEF4', '040FCE43', 'DC3ED60C'],
		'XUSRCB1' : ['D136BF60', 'E4C9F6E1', '87987B7D', '3E56B886', '0169D9ED', '38257732', 'DDD70A64', '2E53C42A'],
		'XUSRCB2' : ['1F5A75DD', 'E772C10A', '86FE99E4', 'BA0D22D5', 'AF1B4D6B', 'E85FD775', '73A59EE2', '9402CDB3'],
		'XUSRCB3' : ['9A83E300', 'D91903E5', '46211725', 'F9C68452', '0AC811A0', '5876B748', 'D676C229', '0232CAC4'],
		'XUSRCBC' : ['EBB46909', '919F175C', '62FCA95D', '703A9318', 'FDC09FAC', '93B9A470', '217E4C25', 'F663A1AF'],
		'XUSRCBG' : ['7DDED0C9', 'EB3FFC55', 'E08F70ED', 'BF1D9B6B', 'EB820E37', '531F2485', '373CDDBE', 'EFA7CCA8'],
		'XUSRNB1' : ['DD44B19C', '0AC8597F', 'F9F8573A', '01C693B1', 'D07CDC76', 'F844A053', '0CC20FFF', '7DC01C22'],
		'XUSRNB2' : ['13287B21', '09736E94', 'F89EB5A3', '859D09E2', '7E0E48F0', '283E0014', 'A2B09B79', 'C79115BB'],
		'XUSRNB3' : ['96F1EDFC', '3718AC7B', '38413B62', 'C656AF65', 'DBDD143B', '98176029', '0763C7B2', '51A112CC'],
		'XUSRNBC' : ['E7C667F5', '7F9EB8C2', '1C9C851A', '4FAAB82F', '2CD59A37', '53D87311', 'F06B49BE', 'A5F079A7'],
		'XUSRNBG' : ['71ACDE35', '053E53CB', '9EEF5CAA', '808DB05C', '3A970BAC', '937EF3E4', 'E629D825', 'BC3414A0'],
		'XUSSCA2' : ['55EE7C0F', '63CDB54E', '00CD080E', '9EEBC35A', '7115DE4D', 'D82DE93F', 'ADAB0DC4', '32365C20'],
		'XUSSCB1' : ['40A7D7CE', '6110603C', 'F17974E0', '786DDFE3', '427DA2FA', 'A625DDFE', '9EC37173', '4B347892'],
		'XUSSCB2' : ['8ECB1D73', '62AB57D7', 'F01F9679', 'FC3645B0', 'EC0F367C', '765F7DB9', '30B1E5F5', 'F165710B'],
		'XUSSCB3' : ['0B128BAE', '5CC09538', '30C018B8', 'BFFDE337', '49DC6AB7', 'C6761D84', '9562B93E', '6755767C'],
		'XUSSCBC' : ['7A2501A7', '14468181', '141DA6C0', '3601F47D', 'BED4E4BB', '0DB90EBC', '626A3732', '93041D17'],
		'XUSSCBG' : ['EC4FB867', '6EE66A88', '966E7F70', 'F926FC0E', 'A8967520', 'CD1F8E49', '7428A6A9', '8AC07010']}
	
	for key, items in CarList.items():
		if key == ID or items[0] == ID or items[1] == ID or items[2] == ID or items[3] == ID or items[4] == ID or items[5] == ID or items[6] == ID or items[7] == ID:
			return (key, items)
	return ("NotFound", "NotFound")


def wheel_ids(ID):
	WheelGraphicsResources = {'00118650': 'DD20E574',
							  '00218650': 'CC5D8F0D',
							  '00318650': '75A654E5',
							  '0416650': '08E74620',
							  '1010650': '8C166D0F',
							  '1010651': '63D40631',
							  '1010652': '88E3BD32',
							  '1216800': '1C137C1F',
							  '5420650': 'AE3A6130',
							  '5716650': '63C3F14F',
							  '5716651': '8C019A71',
							  '5816650': '374B32D2',
							  '6116650': '68F1914F',
							  '6116651': '8733FA71',
							  '6116652': '6C044172',
							  '6116654': '611A3135',
							  '6116655': '8ED85A0B',
							  '6116656': '65EFE108',
							  '6220650': 'A5080130',
							  '6220651': '4ACA6A0E',
							  '6220653': '4E3FBA33',
							  '6220655': '4321CA74',
							  '6416650': '5B762FC4',
							  '6616650': 'F3F09E55',
							  '6616651': '1C32F56B',
							  '6616652': 'F7054E68',
							  '6616653': '18C72556',
							  '6616654': 'FA1B3E2F',
							  '6616657': '112C852C',
							  '6718650': 'B0ED490D',
							  '6718651': '5F2F2233',
							  '6718653': '5BDAF20E',
							  '6718654': 'B906E977',
							  '7218650': '2D026617',
							  '7218651': 'C2C00D29',
							  '7218652': '29F7B62A',
							  '7218653': 'C635DD14',
							  '7218654': '24E9C66D',
							  '7318650': '94F9BDFF',
							  '7418650': '0FF8B2E5',
							  '7520650': '90619FBB',
							  '7520652': '94944F86',
							  '08011760': '921A8155',
							  '08011761': '7DD8EA6B',
							  '08011763': '792D3A56',
							  '08011764': '9BF1212F',
							  '08011765': '74334A11',
							  '08011766': '9F04F112',
							  '08011768': '81CDC1A1',
							  '08011769': '6E0FAA9F',
							  '08011771': 'BC5635AB',
							  '08011772': '57618EA8',
							  '08011773': 'B8A3E596',
							  '08011775': 'B5BD95D1',
							  '08017774': 'FA9A2132',
							  '8618650': '2994644E',
							  '8816650': '3E01708B',
							  '8920650': '5B7E5165',
							  '10116650': 'A0602287',
							  '10116651': '4FA249B9',
							  '10118650': '5A862E37',
							  '10216650': 'B11D48FE',
							  '10218650': '4BFB444E',
							  '10218651': 'A4392F70',
							  '10316650': '08E69316',
							  '10318650': 'F2009FA6',
							  '10318651': '1DC2F498',
							  '10318652': 'F6F54F9B',
							  '10318653': '193724A5',
							  '10319650': '2F964623',
							  '10319652': '2B63961E',
							  '10319653': 'C4A1FD20',
							  '10319654': '267DE659',
							  '10418650': '690190BC',
							  '10520650': 'F698BDE2',
							  '10618650': 'C187212D',
							  '10718650': '787CFAC5',
							  '10818650': '2CF43958',
							  '12418650': 'EEA1B5DF',
							  '12518650': '575A6E37',
							  '16116650': 'F3F14B63',
							  '16116651': '1C33205D',
							  '20046650': 'CEA2CC86',
							  '20116650': 'F3FA7903',
							  '20120650': '2F7E8305',
							  '20218650': '18611FCA',
							  '20218651': 'F7A374F4',
							  '20318650': 'A19AC422',
							  '24120650': 'FB4FCF82',
							  '30116650': '745CB240',
							  '30218650': '9FC7D489',
							  '30318650': '263C0F61',
							  '40120650': '884A340D',
							  '45116650': '2E97131D',
							  '45116651': 'C1557823',
							  '45116652': '2A62C320',
							  '50116650': 'D3680548',
							  '50220650': '1E919537',
							  '50220651': 'F153FE09',
							  '50220652': '1A64450A',
							  '50320650': 'A76A4EDF',
							  '50320651': '48A825E1',
							  '50520650': '85909A2D',
							  '50616650': '48690A52',
							  '50920650': 'C06533C9',
							  '50920651': '2FA758F7',
							  '50920652': 'C490E3F4',
							  '51020650': '187FB537',
							  '51020651': 'F7BDDE09',
							  '51020652': '1C8A650A',
							  '51120650': 'A1846EDF',
							  '51220650': 'B0F904A6',
							  '51320650': '0902DF4E',
							  '51418650': 'B46126E2',
							  '51516650': 'F77CF1BA',
							  '51516651': '18BE9A84',
							  '51516652': 'F3892187',
							  '51620650': '3A8561C5',
							  '51720650': '837EBA2D',
							  '51818650': 'F1948F06',
							  '51916650': 'B289585E',
							  '52020650': '31B701C5',
							  '52120650': '884CDA2D',
							  '52120651': '678EB113',
							  '52120652': '8CB90A10',
							  '52220650': '9931B054',
							  '60320650': 'F4F0155B',
							  '60516650': '0A8E3BAF',
							  '60516651': 'E54C5091',
							  '60516652': '0E7BEB92',
							  '60820650': '2A04B3A5',
							  '60920650': '93FF684D',
							  '61018650': '6D871805',
							  '61120650': 'F21E355B',
							  '61220650': 'E3635F22',
							  '61418650': 'E7FB7D66',
							  '61520650': '78625038',
							  '61620650': '691F3A41',
							  '61718650': 'F686171F',
							  '61818650': 'A20ED482',
							  '61916650': 'E11303DA',
							  '62020650': '622D5A41',
							  '62020651': '8DEF317F',
							  '62020652': '66D88A7C',
							  '62120650': 'DBD681A9',
							  '62120651': '3414EA97',
							  '62120652': 'DF235194',
							  '62220650': 'CAABEBD0',
							  '70116650': '0754958F',
							  '70118650': 'FDB2993F',
							  '80118650': '3B30AAEA',
							  '80118651': 'D4F2C1D4',
							  '80118652': '3FC57AD7',
							  '80118653': 'D00711E9',
							  '80220650': '0C2F3625',
							  '80220651': 'E3ED5D1B',
							  '80318650': '93B61B7B',
							  '80416650': 'F25118D1',
							  '80516650': '4BAAC339',
							  '80718650': '19CA7E18',
							  '81018650': '2CA3E093',
							  '81118650': '95583B7B',
							  '81220650': 'A247A7B4',
							  '81318650': '3DDE8AEA',
							  '81418650': 'A6DF85F0',
							  '81520650': '3946A8AE',
							  '82120650': '9AF2793F',
							  '82220650': '8B8F1346',
							  '82220651': '644D7878',
							  '82220652': '8F7AC37B',
							  'TW01800': '5134752B',
							  'TW01800F': 'B3728D85'}
	
	for key, item in WheelGraphicsResources.items():
		if key == ID or item == ID:
			return (key, item)
	return ("NotFound", "NotFound")


def BurnoutLibraryGet():
	spaths = bpy.utils.script_paths()
	for rpath in spaths:
		tpath = rpath + '\\addons\\BurnoutParadise'
		if os.path.exists(tpath):
			npath = '"' + tpath + '"'
			return tpath
	return None
