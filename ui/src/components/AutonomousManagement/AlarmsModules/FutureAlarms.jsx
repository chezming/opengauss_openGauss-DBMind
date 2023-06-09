import React, { Component } from 'react';
import { Button, Card, Checkbox, Col, DatePicker, message, Row, Select, Table } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import ResizeableTitle from '../../common/ResizeableTitle';
import { getFutureAlarmsInterface, getFutureAlarmsInterfaceCount, getSearchMetricInterface } from '../../../api/autonomousManagement';
import { formatTableTitle, formatTimestamp } from '../../../utils/function';

const { Option } = Select;
export default class Alarms extends Component {
  constructor() {
    super()
    this.state = {
      futureTableSource: [],
      columns: [],
      pageSize: 10,
      current: 1,
      total: 0,
      metric_name: '',
      metricnewname: '',
      host: '',
      hostnewname: '',
      start: '',
      group: true,
      options: [],
      loadingFuture: false,
      hostOptionsFilter: [],
      futureHostOptionFilter: [],
      timekey:''
    }
  }
  components = {
    header: {
      cell: ResizeableTitle,
    },
  };
  // 下拉框数据
  async getSearchMetric () {
    const { success, data, msg } = await getSearchMetricInterface()
    if (success) {
      this.setState({options: data})
    } else {
      message.error(msg)
    }
  }
  async getFutureAlarms (pageParams) {
    let params = {
      metric_name: this.state.metric_name === '' ? null : this.state.metric_name,
      instance: this.state.host === '' ? null : this.state.host,
      start: this.state.start === '' ? null : this.state.start,
      group: this.state.group,
      current: pageParams ? pageParams.current : this.state.current,
      pagesize:pageParams ? pageParams.pagesize : this.state.pageSize
    }
    this.setState({ loadingFuture: true });
    const { success, data, msg } = await getFutureAlarmsInterface(params)
    if (success) {
      if (data.header.length > 0) {
        let historyColumObj = {}
        let tableHeader = []
        let hostOptionsFilterArr = []
        data.header.forEach(item => {
          historyColumObj = {
            title: formatTableTitle(item),
            dataIndex: item,
            width: 180,
            key: item,
            ellipsis: true,
            sorter: (a, b) => {
              let aVal = a[item]
              let bVal = b[item]
              let c = isFinite(aVal),
                d = isFinite(bVal);
              return (c !== d && d - c) || (c && d ? aVal - bVal : aVal.localeCompare(bVal));
            }
          }
          tableHeader.push(historyColumObj)
        })
        let res = []
        data.rows.forEach((item, index) => {
          let tabledata = {}
          for (let i = 0; i < data.header.length; i++) {
            tabledata[data.header[i]] = item[i]
            tabledata['key'] = index
            if ((data.header[i] && data.header[i] === 'start_at') || (data.header[i] && data.header[i] === 'end_at')) {
              tabledata[data.header[i]] = formatTimestamp(item[i])
            }
          }
          res.push(tabledata)
        });
        res.forEach((item) => {
          hostOptionsFilterArr.push(item.instance.replace(/(\s*$)/g, ''))
        })
        let hostOptions = this.handleDataDeduplicate(hostOptionsFilterArr)
        this.setState(() => ({
          futureHostOptionFilter: hostOptions,
          loadingFuture: false,
          futureTableSource: res,
          columns: tableHeader,
          pageSize: this.state.pageSize,
          current: this.state.current
        }))
      } else {
        this.setState({
          loadingFuture: false,
          futureTableSource: [],
          columns: [],
        })
      }
    } else {
      this.setState({
        loadingFuture: false,
        futureTableSource: [],
        columns: [],
      })
      message.error(msg)
    }
  }
  async getFutureAlarmsCount () {
    let params = {
      metric_name: this.state.metric_name === '' ? null : this.state.metric_name,
      instance: this.state.host === '' ? null : this.state.host,
      start: this.state.start === '' ? null : this.state.start,
      group: this.state.group
    }
    const { success, data, msg } = await getFutureAlarmsInterfaceCount(params)
    if (success) {
      this.setState(() => ({
        total: data
      }))
    } else {
      message.error(msg)
    }
  }
  handleDataDeduplicate = (value) => {
    let newArr = []
    for (let i = 0; i < value.length; i++) {
      if (newArr.indexOf(value[i]) === -1 && value[i]) {
        newArr.push(value[i])
      }
    }
    return newArr
  }
  onSearch () { }
  // 回调函数，切换下一页
  changePage(current,pageSize){
    let pageParams = {
      current: current,
      pagesize: pageSize,
    };
    this.setState({
      current: current,
    });
    this.getFutureAlarms(pageParams);
  }
    // 回调函数,每页显示多少条
  changePageSize(pageSize,current){
    // 将当前改变的每页条数存到state中
    this.setState({
      pageSize: pageSize
    });
    let pageParams = {
      current: current,
      pagesize: pageSize,
    };
    this.getFutureAlarms(pageParams);
  }
  handleResize = index => (e, { size }) => {
    this.setState(({ columns }) => {
      const nextColumns = [...columns];
      nextColumns[index] = {
        ...nextColumns[index],
        width: size.width,
      };
      return { columns: nextColumns };
    });
  };
  // metric_name
  onChange1 (e) {
    this.setState({ metric_name: e})
  }
  onSearch1 = (value) => {
    if (value) {
      this.setState({
        metric_name: value,
        metricnewname: value
      })
    }
  };
  onBlurSelect1 = () => {
    const value = this.state.metricnewname
    if (value) {
      this.onChange1(value)
      this.setState({
        metricnewname: ''
      })
    }
  }
  // host
  onChange2 (e) {
    this.setState({host: e})
  }
  onSearch2 = (value) => {
    if (value) {
      this.setState({
        host: value,
        hostnewname: value
      })
    }
  };
  onBlurSelect2 = () => {
    const value = this.state.hostnewname
    if (value) {
      this.onChange2(value)
      this.setState({hostnewname: ''})
    }
  }
  // start
  onChangeData = (date, dateString) => {
    if (dateString) {
      this.setState({
        start: new Date(dateString).getTime()
      })
    } else {
      this.setState({start: ''})
    }
  }
  // group
  onChangeGroupCheckbox (e) {
    this.setState({
      group: e.target.checked
    })
  }
  handleSearch () {
    this.getFutureAlarms().then(() => {
      this.getFutureAlarmsCount()
    })
  }
  handleRefresh(){
    this.setState({
      metric_name: '',
      host: '',
      start: '',
      timekey:new Date(),
      group: true,
      pageSize: 10,
      current: 1,
    },()=>{
      this.getFutureAlarms().then(() => {
        this.getFutureAlarmsCount()
      })
    })
  }
  componentDidMount () {
    this.getSearchMetric()
    this.getFutureAlarms().then(() => {
      this.getFutureAlarmsCount()
    })
  }
  render () {
    const columns = this.state.columns.map((col, index) => ({
      ...col,
      onHeaderCell: column => ({
        width: column.width,
        onResize: this.handleResize(index)
      })
    }))
    const paginationProps = {
      showSizeChanger: true,
      showQuickJumper: true,
      showTotal: () => `Total ${this.state.total} items`,
      pageSize: this.state.pageSize,
      current: this.state.current,
      total: this.state.total,
      onShowSizeChange: (current,pageSize) => this.changePageSize(pageSize,current),
      onChange: (current,pageSize) => this.changePage(current,pageSize)
    };
    return (
      <div>
        <Card title="Future Alarms" extra={<ReloadOutlined className="more_link" onClick={() => { this.handleRefresh() }} />}>
          <Row style={{ marginBottom: 20, width: '60%' }} justify="space-around">
            <Col>
              <span>metric name: </span>
              <Select placeholder="search metric" value={this.state.metric_name} showSearch allowClear={true} onChange={(ev) => { this.onChange1(ev) }}
                onSearch={(e) => { this.onSearch1(e) }} onBlur={() => this.onBlurSelect1()}
                optionFilterProp="children" filterOption={(input, option) =>
                  option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                } style={{ width: 200 }}>
                {
                  this.state.options.map((item, index) => {
                    return (
                      <Option value={item} key={index}>{item}</Option>
                    )
                  })
                }
              </Select>
            </Col>
            <Col>
              <span>host: </span>
              <Select showSearch allowClear={true} value={this.state.host} onChange={(ev) => { this.onChange2(ev) }}
                onSearch={(e) => { this.onSearch2(e) }} onBlur={() => this.onBlurSelect2()} optionFilterProp="children" filterOption={(input, option) =>
                  option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                } style={{ width: 200 }}>
                {
                  this.state.futureHostOptionFilter.map((item, index) => {
                    return (
                      <Option value={item} key={index}>{item}</Option>
                    )
                  })
                }
              </Select>
            </Col>
            <Col>
              <span>start: </span>
              <DatePicker key={this.state.timekey} showTime onChange={(date, dateString) => this.onChangeData(date, dateString)} />
            </Col>
            <Col style={{paddingTop:4}}>
              <span>group: </span>
              <Checkbox checked={this.state.group} onChange={(e) => { this.onChangeGroupCheckbox(e) }}></Checkbox>
            </Col>
            <Col>
              <Button type="primary" onClick={() => this.handleSearch()}>Search</Button>
            </Col>
          </Row>
          <Table bordered showSorterTooltip={false} components={this.components} columns={columns} dataSource={this.state.futureTableSource} rowKey={record => record.key} pagination={paginationProps} loading={this.state.loadingFuture} scroll={{ x: '100%' }} />
        </Card>
      </div>
    )
  }
}
