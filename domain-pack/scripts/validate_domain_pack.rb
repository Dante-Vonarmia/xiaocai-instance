#!/usr/bin/env ruby
# frozen_string_literal: true

require "yaml"
require "set"
require "date"

ROOT = File.expand_path("..", __dir__)
SCHEMA_DIR = File.join(ROOT, "schema")
WORKFLOW_DIR = File.join(ROOT, "workflows")
CATEGORY_DIR = File.join(ROOT, "category-fields")
CONTRACTS_DIR = File.join(ROOT, "contracts")
SCENARIOS_DIR = File.join(CONTRACTS_DIR, "scenarios")

FIELD_DICTIONARY_PATH = File.join(SCHEMA_DIR, "procurement-field-dictionary.yaml")
SCHEMA_PATH = File.join(SCHEMA_DIR, "procurement.yaml")
WORKFLOW_PATH = File.join(WORKFLOW_DIR, "procurement-workflow-nodes.yaml")
CATEGORY_PATH = File.join(CATEGORY_DIR, "procurement-category-fields.yaml")
SEARCH_SOURCING_REPLACE_CONTRACT_PATH = File.join(CONTRACTS_DIR, "procurement-search-sourcing-replace.yaml")
ANALYSIS_RFX_TEMPLATES_CONTRACT_PATH = File.join(CONTRACTS_DIR, "procurement-analysis-rfx-templates.yaml")
FLARE_MAPPING_CONTRACT_PATH = File.join(CONTRACTS_DIR, "flare-contract-mapping.yaml")

FIELD_REQUIRED_KEYS = [
  "字段名称",
  "业务含义",
  "数据口径",
  "必填级别",
  "示例值",
  "类型_枚举_格式",
  "阶段归属"
].freeze

FIELD_NON_EMPTY_KEYS = [
  "业务含义",
  "数据口径",
  "必填级别",
  "示例值",
  "类型_枚举_格式"
].freeze

STAGE_ORDER_BASELINE = ["requirement-collection", "requirement-analysis", "rfx-strategy"].freeze
WORKFLOW_PLACEHOLDERS = ["supplier-search", "quotation", "negotiation", "contract", "delivery"].freeze
EVIDENCE_REQUIRED_FIELDS = %w[source title snippet matched_field candidate_value confidence].freeze
REPLACE_DECISION_MODES = %w[auto_replace_allowed recommend_only user_confirm_required].freeze
REPLACE_HISTORY_REQUIRED_FIELDS = %w[field_key old_value new_candidate evidence_ref decision operator timestamp].freeze
SCENARIO_REQUIRED_FILES = [
  "server-procurement.yaml",
  "event-execution-procurement.yaml",
  "gift-customization-procurement.yaml",
  "content-production-procurement.yaml",
  "travel-service-procurement.yaml"
].freeze

def load_yaml(path, errors)
  YAML.safe_load(File.read(path), permitted_classes: [Date, Time], aliases: false)
rescue StandardError => e
  errors << "[yaml] 解析失败: #{path} => #{e.class}: #{e.message}"
  nil
end

def require_array(value, context, errors)
  unless value.is_a?(Array)
    errors << "[type] #{context} 必须是数组"
    return []
  end
  value
end

def validate_field_dictionary(data, errors)
  return Set.new if data.nil?

  contract = data["contract"]
  unless contract.is_a?(Hash)
    errors << "[dict] 缺少 contract"
    return Set.new
  end

  fields = require_array(data["fields"], "fields", errors)
  field_names = Set.new

  fields.each_with_index do |field, index|
    unless field.is_a?(Hash)
      errors << "[dict] fields[#{index}] 必须是对象"
      next
    end
    FIELD_REQUIRED_KEYS.each do |key|
      errors << "[dict] fields[#{index}] 缺少 #{key}" unless field.key?(key)
    end
    name = field["字段名称"]
    errors << "[dict] fields[#{index}] 字段名称为空" if name.to_s.strip.empty?
    errors << "[dict] 字段名称重复: #{name}" if field_names.include?(name)
    field_names << name

    stages = field["阶段归属"]
    unless stages.is_a?(Array) && !stages.empty?
      errors << "[dict] 字段 #{name} 的 阶段归属 必须是非空数组"
    end

    FIELD_NON_EMPTY_KEYS.each do |key|
      errors << "[dict] 字段 #{name} 的 #{key} 不能为空" if field[key].to_s.strip.empty?
    end
  end

  module_index = data["module_index"]
  if module_index.is_a?(Hash)
    module_index.each do |module_name, module_fields|
      require_array(module_fields, "dict.module_index.#{module_name}", errors).each do |field|
        errors << "[dict] module_index.#{module_name} 包含未定义字段: #{field}" unless field_names.include?(field)
      end
    end
  else
    errors << "[dict] 缺少 module_index"
  end

  declared_count = contract["field_count"]
  if declared_count != field_names.size
    errors << "[dict] contract.field_count=#{declared_count} 与实际字段数 #{field_names.size} 不一致"
  end

  field_names
end

def validate_schema(data, field_names, errors)
  return if data.nil?

  schema = data["schema"]
  unless schema.is_a?(Hash)
    errors << "[schema] 缺少 schema 根节点"
    return
  end

  expected_ref = "schema/procurement-field-dictionary.yaml"
  if schema["field_dictionary_ref"] != expected_ref
    errors << "[schema] schema.field_dictionary_ref 必须为 #{expected_ref}"
  end

  stage_field_sets = data["stage_field_sets"]
  unless stage_field_sets.is_a?(Hash)
    errors << "[schema] 缺少 stage_field_sets"
    return
  end

  stage_field_sets.each do |stage_name, fields|
    require_array(fields, "schema.stage_field_sets.#{stage_name}", errors).each do |field|
      errors << "[schema] stage_field_sets.#{stage_name} 包含未定义字段: #{field}" unless field_names.include?(field)
    end
  end

  entities = data["entities"]
  unless entities.is_a?(Hash)
    errors << "[schema] 缺少 entities"
    return
  end

  entities.each do |entity_name, entity_def|
    refs = entity_def.is_a?(Hash) ? entity_def["field_refs"] : nil
    require_array(refs, "schema.entities.#{entity_name}.field_refs", errors).each do |field|
      errors << "[schema] entities.#{entity_name}.field_refs 包含未定义字段: #{field}" unless field_names.include?(field)
    end
  end
end

def extract_stage_set_name(required_set_ref)
  prefix = "schema/procurement.yaml#stage_field_sets."
  return nil unless required_set_ref.is_a?(String) && required_set_ref.start_with?(prefix)
  required_set_ref.delete_prefix(prefix)
end

def validate_workflow(data, schema_data, field_names, errors)
  return if data.nil?

  stage_order = require_array(data["stage_order"], "workflow.stage_order", errors)
  if stage_order != STAGE_ORDER_BASELINE
    errors << "[workflow] stage_order 必须严格为 #{STAGE_ORDER_BASELINE.join(' -> ')}"
  end

  nodes = data["nodes"]
  unless nodes.is_a?(Hash)
    errors << "[workflow] 缺少 nodes"
    return
  end

  STAGE_ORDER_BASELINE.each do |node_id|
    errors << "[workflow] 缺少首轮节点 #{node_id}" unless nodes.key?(node_id)
  end

  stage_field_sets = schema_data.is_a?(Hash) ? schema_data["stage_field_sets"] : nil
  stage_field_sets ||= {}

  STAGE_ORDER_BASELINE.each do |node_id|
    node = nodes[node_id]
    next unless node.is_a?(Hash)

    require_array(node["inputs"], "workflow.nodes.#{node_id}.inputs", errors)
    require_array(node["outputs"], "workflow.nodes.#{node_id}.outputs", errors)

    field_contract = node["field_contract"]
    unless field_contract.is_a?(Hash)
      errors << "[workflow] workflow.nodes.#{node_id} 缺少 field_contract"
      next
    end

    if field_contract["dictionary_ref"] != "schema/procurement-field-dictionary.yaml"
      errors << "[workflow] #{node_id}.field_contract.dictionary_ref 必须引用字段总表"
    end

    required_set_ref = field_contract["required_set_ref"]
    stage_set_name = extract_stage_set_name(required_set_ref)
    if stage_set_name.nil? || !stage_field_sets.key?(stage_set_name)
      errors << "[workflow] #{node_id}.field_contract.required_set_ref 无法匹配 schema.stage_field_sets"
    end

    %w[initial_required_fields progressive_required_fields must_enrich_fields required_fields].each do |key|
      next unless field_contract.key?(key)
      require_array(field_contract[key], "workflow.nodes.#{node_id}.field_contract.#{key}", errors).each do |field|
        errors << "[workflow] #{node_id}.field_contract.#{key} 包含未定义字段: #{field}" unless field_names.include?(field)
      end
    end

    orchestration = node["orchestration"]
    unless orchestration.is_a?(Hash)
      errors << "[workflow] workflow.nodes.#{node_id} 缺少 orchestration"
      next
    end

    completion = orchestration["completion_rule"]
    unless completion.is_a?(Hash) && !completion["pass_when"].to_s.strip.empty?
      errors << "[workflow] #{node_id}.orchestration.completion_rule.pass_when 缺失"
    end

    require_array(orchestration["output_contract"], "workflow.nodes.#{node_id}.orchestration.output_contract", errors).each do |field|
      errors << "[workflow] #{node_id}.orchestration.output_contract 包含未定义字段: #{field}" unless field_names.include?(field)
    end

    transitions = require_array(node["transitions"], "workflow.nodes.#{node_id}.transitions", errors)
    transitions.each_with_index do |t, index|
      unless t.is_a?(Hash) && t["to"].is_a?(String) && t["condition"].is_a?(String)
        errors << "[workflow] #{node_id}.transitions[#{index}] 必须包含 to/condition"
      end
    end
  end

  placeholders = data["placeholders"]
  unless placeholders.is_a?(Hash)
    errors << "[workflow] 缺少 placeholders"
    return
  end
  WORKFLOW_PLACEHOLDERS.each do |key|
    if !placeholders.key?(key)
      errors << "[workflow] 缺少占位节点 #{key}"
      next
    end
    status = placeholders.dig(key, "status")
    errors << "[workflow] 占位节点 #{key} 的 status 必须是 placeholder" unless status == "placeholder"
  end
end

def validate_categories(data, errors)
  return if data.nil?

  roots = require_array(data["采购负责类"], "category-fields.采购负责类", errors)
  declared_root_count = data.dig("directory", "采购负责类数量")
  if declared_root_count != roots.size
    errors << "[category] directory.采购负责类数量=#{declared_root_count} 与实际 #{roots.size} 不一致"
  end

  lvl1_count = 0
  lvl2_count = 0
  roots.each_with_index do |group, gi|
    unless group.is_a?(Hash)
      errors << "[category] 采购负责类[#{gi}] 必须是对象"
      next
    end
    first_levels = require_array(group["一级品类"], "category-fields.采购负责类[#{gi}].一级品类", errors)
    lvl1_count += first_levels.size

    first_levels.each_with_index do |lv1, li|
      second_levels = require_array(lv1["二级品类"], "category-fields.采购负责类[#{gi}].一级品类[#{li}].二级品类", errors)
      lvl2_count += second_levels.size
      second_levels.each_with_index do |lv2, si|
        %w[各品类特殊需求字段占位 各品类特殊寻源要素占位].each do |key|
          unless lv2[key].is_a?(Array)
            errors << "[category] #{group['名称']}/#{lv1['名称']}/#{lv2['名称']} 缺少或错误: #{key}"
          end
        end
      end
    end
  end

  declared_lvl1 = data.dig("directory", "一级品类数量")
  declared_lvl2 = data.dig("directory", "二级品类数量")
  errors << "[category] directory.一级品类数量=#{declared_lvl1} 与实际 #{lvl1_count} 不一致" if declared_lvl1 != lvl1_count
  errors << "[category] directory.二级品类数量=#{declared_lvl2} 与实际 #{lvl2_count} 不一致" if declared_lvl2 != lvl2_count
end

def validate_search_sourcing_replace_contract(data, field_names, errors)
  return if data.nil?

  contract = data["contract"]
  unless contract.is_a?(Hash) && contract["field_dictionary_ref"] == "schema/procurement-field-dictionary.yaml"
    errors << "[contract:ssr] contract.field_dictionary_ref 必须为 schema/procurement-field-dictionary.yaml"
  end

  mappings = require_array(data["search_mapping"], "contract:ssr.search_mapping", errors)
  mappings.each_with_index do |mapping, idx|
    unless mapping.is_a?(Hash)
      errors << "[contract:ssr] search_mapping[#{idx}] 必须是对象"
      next
    end
    target_field = mapping["target_field"]
    errors << "[contract:ssr] search_mapping[#{idx}] target_field 缺失" if target_field.to_s.strip.empty?
    errors << "[contract:ssr] search_mapping[#{idx}] target_field 未定义: #{target_field}" unless field_names.include?(target_field)

    constraints = mapping["query_constraints"]
    unless constraints.is_a?(Hash)
      errors << "[contract:ssr] search_mapping[#{idx}] query_constraints 缺失"
    else
      %w[required_inputs optional_inputs].each do |k|
        require_array(constraints[k], "contract:ssr.search_mapping[#{idx}].query_constraints.#{k}", errors).each do |field|
          errors << "[contract:ssr] search_mapping[#{idx}] query_constraints.#{k} 未定义字段: #{field}" unless field_names.include?(field)
        end
      end
    end

    evidence = mapping["evidence_contract"]
    unless evidence.is_a?(Hash)
      errors << "[contract:ssr] search_mapping[#{idx}] evidence_contract 缺失"
    else
      required_fields = require_array(evidence["required_fields"], "contract:ssr.search_mapping[#{idx}].evidence_contract.required_fields", errors)
      EVIDENCE_REQUIRED_FIELDS.each do |f|
        errors << "[contract:ssr] search_mapping[#{idx}] evidence_contract.required_fields 缺少 #{f}" unless required_fields.include?(f)
      end
      require_array(evidence["mapped_field_refs"], "contract:ssr.search_mapping[#{idx}].evidence_contract.mapped_field_refs", errors).each do |field|
        errors << "[contract:ssr] search_mapping[#{idx}] evidence mapped_field_refs 未定义字段: #{field}" unless field_names.include?(field)
      end
    end

    candidate_mapping = mapping["candidate_mapping"]
    unless candidate_mapping.is_a?(Hash)
      errors << "[contract:ssr] search_mapping[#{idx}] candidate_mapping 缺失"
    else
      %w[matched_field candidate_value_field].each do |k|
        field = candidate_mapping[k]
        errors << "[contract:ssr] search_mapping[#{idx}] #{k} 缺失" if field.to_s.strip.empty?
        errors << "[contract:ssr] search_mapping[#{idx}] #{k} 未定义字段: #{field}" unless field_names.include?(field)
      end
      min_conf = candidate_mapping["min_confidence"]
      unless min_conf.is_a?(Numeric) && min_conf >= 0.0 && min_conf <= 1.0
        errors << "[contract:ssr] search_mapping[#{idx}] min_confidence 必须在 0~1"
      end
    end
  end

  sourcing = data["sourcing_rules"]
  unless sourcing.is_a?(Hash)
    errors << "[contract:ssr] sourcing_rules 缺失"
  else
    require_array(sourcing["required_requirement_fields"], "contract:ssr.sourcing_rules.required_requirement_fields", errors).each do |field|
      errors << "[contract:ssr] sourcing required_requirement_fields 未定义字段: #{field}" unless field_names.include?(field)
    end
    recommendation = sourcing["recommendation_contract"]
    unless recommendation.is_a?(Hash)
      errors << "[contract:ssr] sourcing recommendation_contract 缺失"
    else
      %w[required_fields rationale_fields].each do |k|
        require_array(recommendation[k], "contract:ssr.sourcing_rules.recommendation_contract.#{k}", errors).each do |field|
          errors << "[contract:ssr] sourcing recommendation #{k} 未定义字段: #{field}" unless field_names.include?(field)
        end
      end
    end
    candidate_pool = sourcing["candidate_pool_policy"]
    unless candidate_pool.is_a?(Hash) && candidate_pool["default_candidate_count"].to_i > 0
      errors << "[contract:ssr] sourcing candidate_pool_policy.default_candidate_count 必须大于0"
    end
    allow_new_supplier_field = candidate_pool.is_a?(Hash) ? candidate_pool["allow_new_supplier_field"] : nil
    unless field_names.include?(allow_new_supplier_field)
      errors << "[contract:ssr] sourcing allow_new_supplier_field 未定义字段: #{allow_new_supplier_field}"
    end
  end

  replace_rules = data["replace_rules"]
  unless replace_rules.is_a?(Hash)
    errors << "[contract:ssr] replace_rules 缺失"
  else
    collected = {}
    REPLACE_DECISION_MODES.each do |mode|
      list = require_array(replace_rules[mode], "contract:ssr.replace_rules.#{mode}", errors)
      list.each do |field|
        errors << "[contract:ssr] replace_rules.#{mode} 未定义字段: #{field}" unless field_names.include?(field)
        collected[field] ||= []
        collected[field] << mode
      end
    end
    collected.each do |field, modes|
      errors << "[contract:ssr] 字段 #{field} 同时出现在多个 replace 模式: #{modes.join(',')}" if modes.size > 1
    end
  end

  history = data["replace_history_contract"]
  unless history.is_a?(Hash)
    errors << "[contract:ssr] replace_history_contract 缺失"
  else
    required = require_array(history["required_fields"], "contract:ssr.replace_history_contract.required_fields", errors)
    REPLACE_HISTORY_REQUIRED_FIELDS.each do |f|
      errors << "[contract:ssr] replace_history_contract.required_fields 缺少 #{f}" unless required.include?(f)
    end
    decisions = require_array(history["decision_enum"], "contract:ssr.replace_history_contract.decision_enum", errors)
    %w[accepted rejected pending].each do |d|
      errors << "[contract:ssr] replace_history_contract.decision_enum 缺少 #{d}" unless decisions.include?(d)
    end
  end
end

def validate_analysis_rfx_templates_contract(data, field_names, errors)
  return if data.nil?

  contract = data["contract"]
  unless contract.is_a?(Hash) && contract["field_dictionary_ref"] == "schema/procurement-field-dictionary.yaml"
    errors << "[contract:templates] contract.field_dictionary_ref 必须为 schema/procurement-field-dictionary.yaml"
  end

  analysis = data["analysis_template"]
  unless analysis.is_a?(Hash)
    errors << "[contract:templates] analysis_template 缺失"
  else
    sections = require_array(analysis["sections"], "contract:templates.analysis_template.sections", errors)
    sections.each_with_index do |section, idx|
      unless section.is_a?(Hash)
        errors << "[contract:templates] analysis_template.sections[#{idx}] 必须是对象"
        next
      end
      %w[id title].each do |k|
        errors << "[contract:templates] analysis_template.sections[#{idx}] 缺少 #{k}" if section[k].to_s.strip.empty?
      end
      %w[required_fields optional_fields].each do |k|
        require_array(section[k], "contract:templates.analysis_template.sections[#{idx}].#{k}", errors).each do |field|
          errors << "[contract:templates] analysis section #{section['id']} #{k} 未定义字段: #{field}" unless field_names.include?(field)
        end
      end
      errors << "[contract:templates] analysis section #{section['id']} 缺少 block_on_missing_required 布尔值" unless [true, false].include?(section["block_on_missing_required"])
    end
  end

  rfx = data["rfx_templates"]
  unless rfx.is_a?(Hash)
    errors << "[contract:templates] rfx_templates 缺失"
  else
    allowed_types = require_array(rfx["allowed_types"], "contract:templates.rfx_templates.allowed_types", errors)
    %w[RFI RFQ RFP RFB].each do |type|
      errors << "[contract:templates] allowed_types 缺少 #{type}" unless allowed_types.include?(type)
    end
    templates = require_array(rfx["templates"], "contract:templates.rfx_templates.templates", errors)
    templates.each_with_index do |tpl, idx|
      unless tpl.is_a?(Hash)
        errors << "[contract:templates] templates[#{idx}] 必须是对象"
        next
      end
      type = tpl["type"]
      errors << "[contract:templates] templates[#{idx}] type 未在 allowed_types 中: #{type}" unless allowed_types.include?(type)
      %w[required_fields optional_fields].each do |k|
        require_array(tpl[k], "contract:templates.templates[#{idx}].#{k}", errors).each do |field|
          errors << "[contract:templates] template #{type} #{k} 未定义字段: #{field}" unless field_names.include?(field)
        end
      end
      bindings = tpl["variable_bindings"]
      unless bindings.is_a?(Hash) && !bindings.empty?
        errors << "[contract:templates] template #{type} variable_bindings 不能为空"
      else
        bindings.each do |var, field|
          errors << "[contract:templates] template #{type} 变量 #{var} 映射未定义字段: #{field}" unless field_names.include?(field)
        end
      end
    end
  end

  states = data["output_state_rules"]
  unless states.is_a?(Hash)
    errors << "[contract:templates] output_state_rules 缺失"
  else
    %w[draft confirmed].each do |state|
      config = states[state]
      unless config.is_a?(Hash)
        errors << "[contract:templates] output_state_rules.#{state} 缺失"
        next
      end
      unless [true, false].include?(config["require_user_confirmation"])
        errors << "[contract:templates] output_state_rules.#{state}.require_user_confirmation 必须是布尔值"
      end
      unless [true, false].include?(config["allow_missing_optional_fields"])
        errors << "[contract:templates] output_state_rules.#{state}.allow_missing_optional_fields 必须是布尔值"
      end
    end
  end
end

def validate_scenarios(field_names, errors)
  scenario_files = Dir.glob(File.join(SCENARIOS_DIR, "*.yaml")).sort
  missing = SCENARIO_REQUIRED_FILES.reject { |f| scenario_files.include?(File.join(SCENARIOS_DIR, f)) }
  missing.each { |f| errors << "[scenarios] 缺少场景文件 #{f}" }

  scenario_files.each do |path|
    data = load_yaml(path, errors)
    next if data.nil?

    scenario = data["scenario"]
    unless scenario.is_a?(Hash)
      errors << "[scenarios] #{File.basename(path)} 缺少 scenario 节点"
      next
    end
    %w[id name].each do |k|
      errors << "[scenarios] #{File.basename(path)} scenario.#{k} 不能为空" if scenario[k].to_s.strip.empty?
    end
    category_path = scenario["category_path"]
    unless category_path.is_a?(Hash)
      errors << "[scenarios] #{File.basename(path)} scenario.category_path 缺失"
    else
      %w[一级品类 二级品类].each do |k|
        errors << "[scenarios] #{File.basename(path)} scenario.category_path.#{k} 不能为空" if category_path[k].to_s.strip.empty?
      end
    end

    input = data["input"]
    unless input.is_a?(Hash) && input["user_message"].to_s.strip != ""
      errors << "[scenarios] #{File.basename(path)} input.user_message 不能为空"
    end
    require_array(input.is_a?(Hash) ? input["attachments"] : nil, "scenarios.#{File.basename(path)}.input.attachments", errors)

    expected = data["expected"]
    unless expected.is_a?(Hash)
      errors << "[scenarios] #{File.basename(path)} expected 缺失"
      next
    end

    classification = expected["classification"]
    unless classification.is_a?(Hash)
      errors << "[scenarios] #{File.basename(path)} expected.classification 缺失"
    else
      %w[一级品类 二级品类].each do |k|
        errors << "[scenarios] #{File.basename(path)} expected.classification.#{k} 不能为空" if classification[k].to_s.strip.empty?
      end
    end

    require_array(expected["required_fields_present"], "scenarios.#{File.basename(path)}.expected.required_fields_present", errors).each do |field|
      errors << "[scenarios] #{File.basename(path)} required_fields_present 未定义字段: #{field}" unless field_names.include?(field)
    end

    blocker = expected["blocker"]
    chooser = expected["chooser"]
    unless blocker.is_a?(Hash) && [true, false].include?(blocker["should_trigger"])
      errors << "[scenarios] #{File.basename(path)} expected.blocker.should_trigger 必须是布尔值"
    end
    unless chooser.is_a?(Hash) && [true, false].include?(chooser["should_trigger"])
      errors << "[scenarios] #{File.basename(path)} expected.chooser.should_trigger 必须是布尔值"
    end

    search = expected["search"]
    unless search.is_a?(Hash)
      errors << "[scenarios] #{File.basename(path)} expected.search 缺失"
    else
      require_array(search["target_fields"], "scenarios.#{File.basename(path)}.expected.search.target_fields", errors).each do |field|
        errors << "[scenarios] #{File.basename(path)} search.target_fields 未定义字段: #{field}" unless field_names.include?(field)
      end
      errors << "[scenarios] #{File.basename(path)} expected.search.expected_query_intent 不能为空" if search["expected_query_intent"].to_s.strip.empty?
    end

    replace = expected["replace"]
    unless replace.is_a?(Hash)
      errors << "[scenarios] #{File.basename(path)} expected.replace 缺失"
    else
      candidate_field = replace["candidate_field"]
      errors << "[scenarios] #{File.basename(path)} replace.candidate_field 未定义字段: #{candidate_field}" unless field_names.include?(candidate_field)
      decision_mode = replace["decision_mode"]
      unless REPLACE_DECISION_MODES.include?(decision_mode)
        errors << "[scenarios] #{File.basename(path)} replace.decision_mode 非法: #{decision_mode}"
      end
    end

    output_assertions = expected["output_assertions"]
    unless output_assertions.is_a?(Hash)
      errors << "[scenarios] #{File.basename(path)} expected.output_assertions 缺失"
    else
      require_array(output_assertions["analysis_sections"], "scenarios.#{File.basename(path)}.expected.output_assertions.analysis_sections", errors)
      rfx_type = output_assertions["rfx_type"]
      errors << "[scenarios] #{File.basename(path)} output_assertions.rfx_type 非法: #{rfx_type}" unless %w[RFI RFQ RFP RFB].include?(rfx_type)
    end
  end
end

def validate_flare_mapping_contract(data, errors)
  return if data.nil?

  contract = data["contract"]
  unless contract.is_a?(Hash) && contract["name"] == "flare-contract-mapping"
    errors << "[contract:flare] contract.name 必须为 flare-contract-mapping"
  end

  mappings = require_array(data["mapping"], "contract:flare.mapping", errors)
  mappings.each_with_index do |item, idx|
    unless item.is_a?(Hash)
      errors << "[contract:flare] mapping[#{idx}] 必须是对象"
      next
    end
    %w[domain_contract flare_interface workspace_state_point status].each do |k|
      errors << "[contract:flare] mapping[#{idx}] 缺少 #{k}" if item[k].to_s.strip.empty?
    end
  end

  policy = data["gap_policy"]
  unless policy.is_a?(Hash)
    errors << "[contract:flare] gap_policy 缺失"
  else
    actions = require_array(policy["when_mapping_missing"], "contract:flare.gap_policy.when_mapping_missing", errors)
    has_action = actions.any? { |x| x.is_a?(Hash) && x["action"].to_s.strip != "" }
    errors << "[contract:flare] gap_policy.when_mapping_missing 必须定义 action" unless has_action
  end
end

errors = []
dictionary_data = load_yaml(FIELD_DICTIONARY_PATH, errors)
schema_data = load_yaml(SCHEMA_PATH, errors)
workflow_data = load_yaml(WORKFLOW_PATH, errors)
category_data = load_yaml(CATEGORY_PATH, errors)
search_sourcing_replace_data = load_yaml(SEARCH_SOURCING_REPLACE_CONTRACT_PATH, errors)
analysis_rfx_templates_data = load_yaml(ANALYSIS_RFX_TEMPLATES_CONTRACT_PATH, errors)
flare_mapping_data = load_yaml(FLARE_MAPPING_CONTRACT_PATH, errors)

field_names = validate_field_dictionary(dictionary_data, errors)
validate_schema(schema_data, field_names, errors)
validate_workflow(workflow_data, schema_data, field_names, errors)
validate_categories(category_data, errors)
validate_search_sourcing_replace_contract(search_sourcing_replace_data, field_names, errors)
validate_analysis_rfx_templates_contract(analysis_rfx_templates_data, field_names, errors)
validate_scenarios(field_names, errors)
validate_flare_mapping_contract(flare_mapping_data, errors)

if errors.empty?
  puts "[OK] domain-pack consistency checks passed"
  exit 0
end

puts "[FAIL] domain-pack consistency checks failed (#{errors.size})"
errors.each { |err| puts " - #{err}" }
exit 1
