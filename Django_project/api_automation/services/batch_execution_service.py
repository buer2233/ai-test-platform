"""
batch_execution_service.py

批量执行服务，支持按集合、项目、手动选择三种方式批量执行测试用例。

核心功能：
1. 按集合执行：执行集合中所有测试用例
2. 按项目执行：执行项目下所有测试用例
3. 手动选择执行：执行用户选择的测试用例
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.utils import timezone
from api_automation.models import (
    ApiProject, ApiCollection, ApiTestCase, ApiTestEnvironment,
    ApiTestExecution, ApiTestResult
)
from api_automation.services.http_executor import HttpExecutor
from api_automation.services.assertion_engine import AssertionEngine
from api_automation.services.extraction_engine import ExtractionEngine
from api_automation.services.variable_pool_service import VariablePool
from api_automation.services.result_storage_service import ResultStorageService
from api_automation.services.websocket_service import WebSocketBroadcastService

logger = logging.getLogger(__name__)


class BatchExecutionService:
    """
    批量执行服务
    """

    def __init__(self):
        self.variable_pool = None
        self.websocket = WebSocketBroadcastService()
        self.executor = None

    def execute_by_collection(
        self,
        collection_id: int,
        environment_id: int,
        user_id: int,
        execution_name: Optional[str] = None,
    ) -> ApiTestExecution:
        """
        按集合执行测试

        Args:
            collection_id: 集合ID
            environment_id: 环境ID
            user_id: 执行用户ID
            execution_name: 执行名称（可选）

        Returns:
            ApiTestExecution实例
        """
        try:
            # 获取集合
            collection = ApiCollection.objects.get(id=collection_id)
            environment = ApiTestEnvironment.objects.get(id=environment_id)

            # 获取集合中所有测试用例
            test_cases = list(collection.test_cases.filter(is_deleted=False))

            if not test_cases:
                raise ValueError(f"集合 {collection.name} 中没有测试用例")

            # 创建执行记录
            execution = self._create_execution(
                project=collection.project,
                environment=environment,
                test_cases=test_cases,
                user_id=user_id,
                name=execution_name or f"执行集合: {collection.name}",
                description=f"按集合执行: {collection.name}",
            )

            # 执行测试
            self._execute_batch(execution, test_cases, environment)

            return execution

        except Exception as e:
            logger.error(f"Error executing by collection: {e}")
            raise

    def execute_by_project(
        self,
        project_id: int,
        environment_id: int,
        user_id: int,
        execution_name: Optional[str] = None,
    ) -> ApiTestExecution:
        """
        按项目执行所有测试用例

        Args:
            project_id: 项目ID
            environment_id: 环境ID
            user_id: 执行用户ID
            execution_name: 执行名称（可选）

        Returns:
            ApiTestExecution实例
        """
        try:
            # 获取项目和环境
            project = ApiProject.objects.get(id=project_id)
            environment = ApiTestEnvironment.objects.get(id=environment_id)

            # 获取项目下所有测试用例（包括未分配到集合的）
            test_cases = list(project.test_cases.filter(is_deleted=False))

            if not test_cases:
                raise ValueError(f"项目 {project.name} 中没有测试用例")

            # 创建执行记录
            execution = self._create_execution(
                project=project,
                environment=environment,
                test_cases=test_cases,
                user_id=user_id,
                name=execution_name or f"执行项目: {project.name}",
                description=f"按项目执行所有用例: {project.name}",
            )

            # 执行测试
            self._execute_batch(execution, test_cases, environment)

            return execution

        except Exception as e:
            logger.error(f"Error executing by project: {e}")
            raise

    def execute_by_selection(
        self,
        test_case_ids: List[int],
        environment_id: int,
        user_id: int,
        execution_name: Optional[str] = None,
    ) -> ApiTestExecution:
        """
        按手动选择的测试用例执行

        Args:
            test_case_ids: 测试用例ID列表
            environment_id: 环境ID
            user_id: 执行用户ID
            execution_name: 执行名称（可选）

        Returns:
            ApiTestExecution实例
        """
        try:
            # 验证所有用例属于同一项目
            test_cases = []
            project_id = None

            for tc_id in test_case_ids:
                test_case = ApiTestCase.objects.get(id=tc_id)
                if project_id is None:
                    project_id = test_case.project_id
                elif test_case.project_id != project_id:
                    raise ValueError("所选测试用例必须属于同一项目")

                test_cases.append(test_case)

            if not test_cases:
                raise ValueError("未选择任何测试用例")

            # 获取环境和项目
            environment = ApiTestEnvironment.objects.get(id=environment_id)
            project = ApiProject.objects.get(id=project_id)

            # 创建执行记录
            execution = self._create_execution(
                project=project,
                environment=environment,
                test_cases=test_cases,
                user_id=user_id,
                name=execution_name or f"手动执行: {len(test_cases)}个用例",
                description=f"手动选择的测试用例",
            )

            # 执行测试
            self._execute_batch(execution, test_cases, environment)

            return execution

        except Exception as e:
            logger.error(f"Error executing by selection: {e}")
            raise

    def _create_execution(
        self,
        project: ApiProject,
        environment: ApiTestEnvironment,
        test_cases: List[ApiTestCase],
        user_id: int,
        name: str,
        description: Optional[str] = None,
    ) -> ApiTestExecution:
        """
        创建执行记录

        Args:
            project: 项目对象
            environment: 环境对象
            test_cases: 测试用例列表
            user_id: 用户ID
            name: 执行名称
            description: 执行描述

        Returns:
            ApiTestExecution实例
        """
        execution = ApiTestExecution.objects.create(
            name=name,
            description=description or '',
            project=project,
            environment=environment,
            test_cases=[tc.id for tc in test_cases],
            status='PENDING',
            total_count=len(test_cases),
            passed_count=0,
            failed_count=0,
            skipped_count=0,
            created_by_id=user_id,
        )

        logger.info(f"Created execution: {execution.name} with {len(test_cases)} test cases")
        return execution

    def _execute_batch(
        self,
        execution: ApiTestExecution,
        test_cases: List[ApiTestCase],
        environment: ApiTestEnvironment,
    ):
        """
        批量执行测试用例

        Args:
            execution: 执行记录
            test_cases: 测试用例列表
            environment: 测试环境
        """
        try:
            # 更新执行状态为运行中
            execution.status = 'RUNNING'
            execution.start_time = timezone.now()
            execution.save()

            # 初始化变量池
            self.variable_pool = VariablePool(environment)
            self.executor = HttpExecutor()

            # 通过WebSocket通知执行开始
            self.websocket.broadcast_execution_update(
                execution.id,
                {'status': 'RUNNING', 'message': '开始执行批量测试'}
            )

            # 按顺序执行每个测试用例
            for index, test_case in enumerate(test_cases):
                try:
                    # 执行单个测试用例
                    self._execute_single_test_case(
                        execution=execution,
                        test_case=test_case,
                        environment=environment,
                        index=index,
                        total=len(test_cases),
                    )

                except Exception as e:
                    logger.error(f"Error executing test case {test_case.name}: {e}")
                    # 创建错误结果
                    self._create_error_result(execution, test_case, str(e))

            # 更新执行状态为完成
            execution.status = 'COMPLETED'
            execution.end_time = timezone.now()

            # 计算执行时长
            if execution.start_time and execution.end_time:
                duration = (execution.end_time - execution.start_time).total_seconds()
                execution.duration = int(duration)

            execution.save()

            # 通过WebSocket通知执行完成
            self.websocket.broadcast_execution_update(
                execution.id,
                {
                    'status': 'COMPLETED',
                    'passed_count': execution.passed_count,
                    'failed_count': execution.failed_count,
                    'skipped_count': execution.skipped_count,
                    'message': '批量测试执行完成'
                }
            )

            logger.info(f"Execution {execution.name} completed: {execution.passed_count} passed, {execution.failed_count} failed")

        except Exception as e:
            logger.error(f"Error in batch execution: {e}")
            execution.status = 'FAILED'
            execution.end_time = timezone.now()
            execution.save()

            self.websocket.broadcast_execution_update(
                execution.id,
                {'status': 'FAILED', 'message': f'批量执行失败: {str(e)}'}
            )
            raise

    def _execute_single_test_case(
        self,
        execution: ApiTestExecution,
        test_case: ApiTestCase,
        environment: ApiTestEnvironment,
        index: int,
        total: int,
    ):
        """
        执行单个测试用例

        Args:
            execution: 执行记录
            test_case: 测试用例
            environment: 测试环境
            index: 当前索引
            total: 总数
        """
        start_time = timezone.now()

        # 通过WebSocket通知当前执行进度
        self.websocket.broadcast_execution_update(
            execution.id,
            {
                'current_index': index,
                'total': total,
                'current_test_case': test_case.name,
                'progress': int((index / total) * 100),
            }
        )

        # 构建请求数据（替换变量）
        request_data = self._build_request_data(test_case, environment)

        # 执行HTTP请求
        http_response = self.executor.execute_request(
            method=request_data['method'],
            url=request_data['url'],
            headers=request_data.get('headers', {}),
            params=request_data.get('params', {}),
            body=request_data.get('body', {}),
        )

        # 构建响应数据
        response_data = self._build_response_data(http_response)

        # 执行断言
        assertion_results = self._execute_assertions(test_case, http_response)

        # 数据提取
        self._execute_extractions(test_case, http_response)

        # 判断测试状态
        status = self._determine_test_status(assertion_results, http_response)

        # 创建测试结果（使用分级存储）
        test_result = ApiTestResult.objects.create(
            execution=execution,
            test_case=test_case,
            status=status,
            response_status=http_response.get('status_code'),
            response_time=http_response.get('response_time', 0),
            request_url=request_data['url'],
            request_method=request_data['method'],
            start_time=start_time,
            end_time=timezone.now(),
        )

        # 使用分级存储服务保存结果
        ResultStorageService.save_result(
            test_result=test_result,
            http_response=http_response,
            request_data=request_data,
            response_data=response_data,
            assertion_results=assertion_results,
        )

        # 更新执行统计
        if status == 'PASSED':
            execution.passed_count += 1
        elif status == 'FAILED':
            execution.failed_count += 1
        else:
            execution.skipped_count += 1

        execution.save()

        logger.debug(f"Test case {test_case.name} completed with status: {status}")

    def _build_request_data(
        self,
        test_case: ApiTestCase,
        environment: ApiTestEnvironment,
    ) -> Dict[str, Any]:
        """
        构建请求数据（替换变量）

        Args:
            test_case: 测试用例
            environment: 测试环境

        Returns:
            请求数据字典
        """
        # 合并环境变量和全局变量
        headers = {**environment.global_headers, **test_case.headers}

        # 替换变量
        url = self.variable_pool.replace_variables(test_case.url)
        headers = self.variable_pool.replace_variables_in_dict(headers)
        params = self.variable_pool.replace_variables_in_dict(test_case.params)
        body = self.variable_pool.replace_variables_in_dict(test_case.body)

        return {
            'method': test_case.method,
            'url': url,
            'base_url': environment.base_url,
            'headers': headers,
            'params': params,
            'body': body,
        }

    def _build_response_data(self, http_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建响应数据

        Args:
            http_response: HTTP响应

        Returns:
            响应数据字典
        """
        return {
            'status_code': http_response.get('status_code'),
            'status_text': http_response.get('status_text', ''),
            'response_time': http_response.get('response_time', 0),
            'headers': http_response.get('headers', {}),
            'body': http_response.get('body', {}),
            'content_length': len(str(http_response.get('body', ''))),
        }

    def _execute_assertions(
        self,
        test_case: ApiTestCase,
        http_response: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        执行断言

        Args:
            test_case: 测试用例
            http_response: HTTP响应

        Returns:
            断言结果列表
        """
        assertion_engine = AssertionEngine()
        results = []

        # 获取用例的所有断言配置
        assertions = test_case.assertions.filter(is_enabled=True)

        for assertion in assertions:
            result = assertion_engine.evaluate(
                assertion=assertion,
                response=http_response,
            )
            results.append(result)

        return results

    def _execute_extractions(
        self,
        test_case: ApiTestCase,
        http_response: Dict[str, Any],
    ):
        """
        执行数据提取，并将提取的变量添加到变量池

        Args:
            test_case: 测试用例
            http_response: HTTP响应
        """
        extraction_engine = ExtractionEngine()

        # 获取用例的所有提取配置
        extractions = test_case.extractions.filter(is_enabled=True)

        for extraction in extractions:
            try:
                value = extraction_engine.extract(
                    extraction=extraction,
                    response=http_response,
                )

                if value is not None:
                    # 根据作用域决定添加到哪个变量池
                    if extraction.variable_scope == 'global':
                        self.variable_pool.add_global_variable(
                            extraction.variable_name, value
                        )
                    else:
                        # 默认添加到共享变量（用例间传递）
                        self.variable_pool.add_shared_variable(
                            extraction.variable_name, value
                        )

                    logger.debug(f"Extracted variable: {extraction.variable_name} = {value}")

            except Exception as e:
                logger.warning(f"Failed to extract {extraction.variable_name}: {e}")

    def _determine_test_status(
        self,
        assertion_results: List[Dict[str, Any]],
        http_response: Dict[str, Any],
    ) -> str:
        """
        判断测试状态

        Args:
            assertion_results: 断言结果列表
            http_response: HTTP响应

        Returns:
            测试状态 (PASSED/FAILED/ERROR)
        """
        # 检查HTTP状态码
        status_code = http_response.get('status_code', 0)

        # 如果HTTP请求失败
        if status_code == 0:
            return 'ERROR'

        # 检查断言结果
        if assertion_results:
            for result in assertion_results:
                if not result.get('passed', False):
                    return 'FAILED'

        return 'PASSED'

    def _create_error_result(
        self,
        execution: ApiTestExecution,
        test_case: ApiTestCase,
        error_message: str,
    ):
        """
        创建错误结果

        Args:
            execution: 执行记录
            test_case: 测试用例
            error_message: 错误信息
        """
        ApiTestResult.objects.create(
            execution=execution,
            test_case=test_case,
            status='ERROR',
            error_message=error_message,
            start_time=timezone.now(),
            end_time=timezone.now(),
        )

        execution.failed_count += 1
        execution.save()
