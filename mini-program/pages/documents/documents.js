import { uploadDocument } from '../../utils/api';

Page({
  data: {
    documents: [],
    uploading: false,
  },

  onShow() {
    // Phase 2 接入 MySQL 后实现真正的列表
  },

  chooseFile() {
    const that = this;
    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      extension: ['pdf', 'docx', 'doc', 'txt', 'md', 'markdown'],
      success(res) {
        const file = res.tempFiles[0];
        that.upload(file.path, file.name);
      },
      fail(err) {
        if (err.errMsg.indexOf('cancel') === -1) {
          wx.showToast({ title: '选择文件失败', icon: 'none' });
        }
      },
    });
  },

  async upload(filePath, fileName) {
    this.setData({ uploading: true });

    try {
      const result = await uploadDocument(filePath, fileName);
      this.setData({
        documents: [result, ...this.data.documents],
      });
      wx.showToast({ title: '上传成功', icon: 'success' });
    } catch (e) {
      wx.showToast({ title: '上传失败: ' + e.message, icon: 'none' });
    } finally {
      this.setData({ uploading: false });
    }
  },

  deleteDoc(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复',
      success: (res) => {
        if (res.confirm) {
          // TODO: Phase 2 接入删除 API
          wx.showToast({ title: '功能开发中', icon: 'none' });
        }
      },
    });
  },
});
