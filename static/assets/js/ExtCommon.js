//관리자 정보 가져오기
function getAdminInfo(admin_id){
  let Admin_Name;
  let Admin_tel_no;
  let TXT_DutyCTA  = '김기현'//책임세무사
  let TXT_DutyCTAHP = '010-9349-7120'//책임세무사 휴대번호
  let TXT_OfficeAddress  = '서울특별시 강남구 강남대로84길 15, 206호(역삼동, 강남역효성해링턴타워더퍼스트)'
  $.ajax({
    url: "{% url 'getAdminInfo' %}",
    data: { admin_id: admin_id},
    dataType: "json"
  }).done(function(response) {
    Admin_Name = response.admin_name;
    Admin_tel_no = response.admin_tel_no;
  }).fail(function(error) {
      console.error(`오류 발생:`, error);
  });
  return { Admin_Name, Admin_tel_no, TXT_DutyCTA, TXT_DutyCTAHP, TXT_OfficeAddress};
}

//현재 연월리턴하기
function getWorkYearAndMonth(flag) {
  let work_MM,work_YY;
  let today = new Date();   

  let year = today.getFullYear(); // 년도
  let month = today.getMonth() + 1;  // 월
  let date = today.getDate();  // 날짜
  let day = today.getDay();  // 요일

  //월변경 기준일
  flagDay = 25
  flagMonth = 2
  if (flag=="scrap_monthly_list"){
    flagDay = 25
  } else if (flag=="kijang_goji_list"){
    flagDay = 10
  } else if (flag=="mng_corp" || flag=="mng_stat" || flag === "mng_statement"){
    flagMonth = 4   
    flagDay = 0
  } else if (flag=="mng_vat") {
    flagMonth = 2
    flagDay = 0
  }
  // alert(flagDay)
  if (month < flagMonth || month === 12) {
    if (date >= flagDay) {
      work_YY = year - 1;
    }else{
      work_YY = year;    
    }
  } else {
    work_YY = year;
  }

  if (date >= flagDay) {
    work_MM = month
  } else {
    work_MM = month - 1
  }
  
  return { work_YY, work_MM };
}

//문자발송 모달열기 
function smsModal(seq_no, hp_no) {
    console.log("1. smsModal 클릭됨:", seq_no, hp_no); // 로그 추가
    
    if (activeTooltip) {
        activeTooltip.destroy();
        activeTooltip = null;
        activeSeqNo = null;
    }  

    if (typeof window.prepareSmsModal === 'function') {
        console.log("2. prepareSmsModal 함수 호출 시도");
        window.prepareSmsModal(seq_no, hp_no || "");
    } else {
        console.error("오류: window.prepareSmsModal 함수가 정의되지 않았습니다. modal.html이 로드되었는지 확인하세요.");
    }
    $("#smsModal").modal('show');
}

//tooltip animation 효과
(function insertTooltipStyles() {
  const styleId = 'custom-tooltip-style';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.innerHTML = `
      @keyframes tooltipFadeIn {
        0% { opacity: 0; transform: scale(0.9); }
        100% { opacity: 1; transform: scale(1); }
      }

      .custom-tooltip-animated {
        animation: tooltipFadeIn 0.2s ease-out;
      }
    `;
    document.head.appendChild(style);
  }
})();
// 전역 (이미 있으시면 생략)
var latestTooltipRequestId = 0;
var activeTooltip = null;
var activeSeqNo = null;

// SEQ 컬럼 클릭 시 툴팁
function attachGridToolTip(grid, urlTemplate) {
  var view = grid.getView();
  var initialMousePos = null;

  // ★ cellIndex + 1 같은 DOM 접근 안 쓰고, Ext의 cellclick 이벤트 사용
  view.on('cellclick', function (view, td, cellIndex, record, tr, rowIndex, e) {
    var columns = view.getHeaderCt().getGridColumns();
    var column  = columns[cellIndex];

    // 디버그 로그: 어떤 컬럼이 클릭됐는지 확인
    console.log('[Tooltip] cellclick', {
      cellIndex      : cellIndex,
      headerText     : column && column.text,
      dataIndex      : column && column.dataIndex,
      seq_no_in_row  : record && record.get && record.get('seq_no')
    });

    // ★ 여기서 dataIndex 로만 필터링
    if (!column || column.dataIndex !== 'seq_no') {
      console.warn('[Tooltip] skip: not seq_no column', column && column.dataIndex);
      return; // SEQ 컬럼이 아니면 아무 것도 안 함
    }

    if (!record) return;

    var seqNo = record.get('seq_no');
    var url   = urlTemplate.replace('{seq_no}', seqNo);

    // 기존 툴팁 제거
    if (activeTooltip) {
      activeTooltip.destroy();
      activeTooltip = null;
      activeSeqNo   = null;
    }

    // 클릭 위치 저장
    initialMousePos = e.getXY();

    var currentRequestId = ++latestTooltipRequestId;

    console.log('[Tooltip] ajax start', url);
    Ext.Ajax.request({
      url   : url,
      method: 'GET',
      success: function (res) {
        if (currentRequestId !== latestTooltipRequestId) return; // 뒤에 또 클릭됐으면 무시

        var data = Ext.decode(res.responseText);
        var profileImageUrl = (data.userprofile && data.userprofile.image) ||
                              '/static/assets/images/faces/blank.jpg';

        activeTooltip = Ext.create('Ext.Component', {
          floating: true,
          renderTo: Ext.getBody(),
          cls: 'custom-tooltip-animated',
          style: {
            background   : '#fff',
            border       : '1px solid #ccc',
            padding      : '12px',
            borderRadius : '8px',
            zIndex       : 10000,
            boxShadow    : '0 2px 10px rgba(0,0,0,0.2)',
            minWidth     : '300px',
            maxWidth     : '500px'
          },
          html: `
            <div>
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center;">
                  <img src="${profileImageUrl}" style="width:48px;height:48px;border-radius:50%;margin-right:10px;">
                  <div>
                    <div><strong>${Ext.String.htmlEncode(data.biz_name)}</strong></div>
                    <div style="color:gray">${Ext.String.htmlEncode(data.ceo_name)}</div>
                  </div>
                </div>
                <button id="tooltipCloseBtn" style="border:none;background:none;font-size:20px;">&times;</button>
              </div>
              <hr>
              <div><strong>사업자번호:</strong> ${Ext.String.htmlEncode(data.biz_no)}</div>
              <div><strong>주민번호:</strong> ${Ext.String.htmlEncode(data.ssn)}</div>
              <hr>
              <div><strong>휴대번호:</strong> <a href="javascript:void(0);" onclick="smsModal('${seqNo}', '${Ext.String.htmlEncode(data.hp_no || '')}');">${Ext.String.htmlEncode(data.hp_no || '')}</a></div>
              <div><strong>이메일:</strong> <a href="mailto:${Ext.String.htmlEncode(data.email)}">${Ext.String.htmlEncode(data.email)}</a></div>
              <div><strong>회사전화:</strong> ${Ext.String.htmlEncode(data.biz_tel)}</div>
              <div><strong>팩스:</strong> ${Ext.String.htmlEncode(data.biz_fax)}</div>
              <hr>
              <div><strong>홈택스 ID/PW:</strong> ${Ext.String.htmlEncode(data.hometaxid)} / ${Ext.String.htmlEncode(data.hometaxpw)}</div>
              <div><strong>세무서:</strong> ${Ext.String.htmlEncode(data.taxmgr_name)}조사관 ${Ext.String.htmlEncode(data.taxmgr_tel)}</div>
              <hr>
              <div><strong>인트라넷:</strong> ${Ext.String.htmlEncode(data.biz_no.replace(/-/g, ''))} / ${Ext.String.htmlEncode(data.user_pwd)}</div>
              <hr>
              <div>${Ext.String.htmlEncode(data.etc)}</div>
            </div>
          `
        });

        // 1차 위치: 클릭 지점 기준
        activeTooltip.setPosition(initialMousePos[0] + 15, initialMousePos[1] + 15);
        activeTooltip.show();
        activeSeqNo = seqNo;

        // 화면 하단 넘어가는 것 방지
        Ext.defer(function () {
          if (!activeTooltip || !activeTooltip.el) return;

          var tipEl     = activeTooltip.el.dom;
          var tipHeight = tipEl.offsetHeight;
          var top       = initialMousePos[1] + 15;

          if (top + tipHeight > window.innerHeight - 10) {
            top = initialMousePos[1] - tipHeight - 15;
          }

          activeTooltip.setPosition(initialMousePos[0] + 15, top);

          var closeButton = document.getElementById('tooltipCloseBtn');
          if (closeButton) {
            closeButton.addEventListener('click', function () {
              if (activeTooltip) {
                activeTooltip.destroy();
                activeTooltip = null;
                activeSeqNo   = null;
              }
            });
          }
        }, 30);
      },
      failure: function (res) {
        if (currentRequestId !== latestTooltipRequestId) return;
        console.error('[Tooltip] ajax failed', res && res.status, res && res.responseText);
        Ext.toast('정보를 불러오지 못했습니다.', 2000);
      }
    });
  });

  // ESC 키 닫기
  Ext.getDoc().on('keydown', function (e) {
    if (e.getKey() === Ext.EventObject.ESC && activeTooltip) {
      activeTooltip.destroy();
      activeTooltip = null;
      activeSeqNo   = null;
    }
  });
}



//********************************** adid Docker start */
// ScrollMenu 생성 함수
function createScrollMenu(arrADID, onItemClickHandler) {
    const scrollMenu = Ext.create('Ext.menu.Menu', {
        height: 500,
        scrollable: {
            x: false,
            y: true
        }
    });

    // 메뉴 항목 추가
    arrADID.forEach(function (item) {
        scrollMenu.add({
            text: item,
            handler: function () {
                onItemClickHandler(item);
            }
        });
    });

    return scrollMenu;
}
// 메뉴 버튼 텍스트 업데이트 함수
function updateScrollMenuText(selectedItem) {
    // 1. 현재 활성화된 탭(tab-pane active)을 찾습니다.
    var activeTab = document.querySelector('div.tab-pane.active');
    if (!activeTab) return;

    // 2. 활성 탭 내부의 ExtJS Grid 요소를 찾습니다.
    var gridEl = activeTab.querySelector('.x-grid');
    
    if (gridEl && gridEl.id) {
        // 3. DOM ID를 이용해 ExtJS 컴포넌트를 가져옵니다.
        var gridCmp = Ext.getCmp(gridEl.id);
        
        if (gridCmp) {
            // 4. 그리드 하위 컴포넌트 중에서 itemId가 'tb_company'인 것을 찾습니다.
            var menuButton = gridCmp.down('#tb_company');
            if (menuButton) {
                menuButton.setText(selectedItem);
            }
        }
    }
}
// Docked Items 생성 함수
function createDockedItemsConfig(adminBizLevel, arrADID, ADID, onItemClickHandler) {
  const dockedItemsConfig = [];
  
  // 권한 체크 로직 (필요에 따라 조건 수정 가능)
  if (adminBizLevel === "세무사" || adminBizLevel === "관리자" || adminBizLevel === "SA") {
    if (arrADID.length <= 20) {
        // 회원 수가 적은 경우 (기존 로직 유지)
        arrADID.forEach(function (item, index) {
            dockedItemsConfig.push({
                text: item,
                enableToggle: true,
                toggleGroup: 'adidGroup',
                pressed: ADID === item,
                handler: function () {
                  onItemClickHandler(item);
                }
            });
            if (index < arrADID.length - 1) {
                dockedItemsConfig.push({ xtype: 'tbseparator' });
            }
        });
    } else {
        // 회원 수가 많은 경우 스크롤 메뉴 사용
        const scrollMenu = createScrollMenu(arrADID, onItemClickHandler);
        dockedItemsConfig.push({
            text: ADID,
            itemId: 'tb_company', // ★ [핵심 수정] id -> itemId 로 변경 (중복 방지)
            iconCls: 'fa fa-bars',
            menu: scrollMenu
        });
    }
  }

  return dockedItemsConfig;
}
//********************************** adid Docker end */

// 메일 보내기 
const sendMail =(seq_no, work_YY, work_MM,flag,objectUrl,targetUrl,user_file_names,user_path)=>{
  // console.log(user_file_names)
  // console.log(user_path)
  showLoading("이메일 발송중 "); // 로딩 마스크 표시
  $.ajax({
    url:  objectUrl,
    type: "POST",
    contentType: "application/json",
    headers: { "X-CSRFToken": "{{ csrf_token }}" },  // Django CSRF 보호
    data: JSON.stringify({
      seq_no: seq_no,
      work_YY:work_YY, 
      work_MM:work_MM,
      mail_class: flag,
      targetUrl:targetUrl,               //admin/mail/template 메일폼
      user_file_names: user_file_names,  // 파일 리스트 ["a.pdf", "b.pdf", "c.pdf"]
      user_path: user_path
    }),    
    success: function() {
      hideLoading(); // 로딩 마스크 숨김
      //sentMailList(seq_no, flag,"{% url 'getSentMails' %}") ;
    },
    error: function() {
      hideLoading(); // 로딩 마스크 숨김
      alert("메일 발송에 실패했습니다.");
    }
  });
}

//알림톡 보내기 ==> url:send_kakao_notification
const sendKakao =(seq_no, work_YY, work_MM,flag,objectUrl)=>{
  showLoading("알림톡 발송중 ");
  $.ajax({
    url: objectUrl,
    type: "POST",
    data: {
      seq_no: seq_no,
      work_YY: work_YY,
      work_MM: work_MM,
      flag : flag,
      csrfmiddlewaretoken: "{{ csrf_token }}"
    },
    dataType: "json",
    success: function (data, textStatus, jqXHR) {
      hideLoading(); // 로딩 마스크 숨김
      if (jqXHR.status === 200 && data.status === "success") {
        //Swal.fire("성공", data.message, "success").then(() => {
          // ✅ 모달 닫기
          $('#summitModal').modal('hide');

          // ✅ 메인 그리드 업데이트 (ExtJS 사용 시)
          let store = Ext.getCmp('mainGrid').getStore();
          let grid = Ext.ComponentQuery.query('gridpanel')[0]; // 첫 번째 그리드 가져오기
          if (grid) {
            let store = grid.getStore();
            let record = store.findRecord('seq_no', seq_no);
            var currentDate = new Date(); // 현재 날짜 및 시간 가져오기
            var formattedDate = Ext.Date.format(currentDate, 'Y-m-d H:i:s'); // YYYY-MM-DD HH:MM:SS 형식으로 변환

            if (record) {
              var sentImg = ""
              if (data.message.substr(0, 2)=="카톡"){
                sentImg = '<img src="/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-kko.png">'
              }else{
                sentImg = '<img src="/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-sns.png">'
              }

              if (flag=="goji"){
                record.set('mailDate', formattedDate);                                
              }else if (flag=="vatElec"){
                record.set('kakaoSentTI', sentImg);
              }else if(flag=="Card"){
                record.set('kakaoSentCard', sentImg); 
              }else if (flag=="VatIntro"){            
                record.set('MailGrade', "😞");                    
              }else if (flag=="VatResult"){            
                record.set('MailGrade', "🙂");                  
              }else if (flag=="CorpIntro"){            
                record.set('MailGrade', "😞");    
              }else if (flag=="CorpResult"){            
                record.set('MailGrade', "🙂");                    
              }else if (flag=="CorpFee"){            
                record.set('MailGrade', "😍");                                    
              }
              store.commitChanges(); // 변경 사항 적용
            }              
          }
        //});
      } else {
        hideLoading(); // 로딩 마스크 숨김
        Swal.fire("오류", "전송오류 : " + jqXHR.responseJSON.message, "error");
      }
    },
    error: function (jqXHR, textStatus, errorThrown) {
      hideLoading(); // 로딩 마스크 숨김
      Swal.fire("전송 실패", "서버에서 오류가 발생했습니다: " + jqXHR.responseJSON.message, "error");
    }
  });
}

//보낸메일함
const sentMailList = async (seq_no, flag,url) => {
  $.ajax({
    url:url,
    type: "POST",
    data: {
      seq_no: seq_no,
      flag: flag
    },
    success: function(response) {
        // 메일 리스트 데이터 가져오기
        const mailList = response.recordset_mail;

        // 테이블 헤더
        let tableHtml = `
          <div class="table-responsive" style="max-height: 600px; overflow-y: auto;">
          <table class="table table-striped table-bordered">
              <thead class="table-light">
                  <tr>
                      <th>#</th>
                      <th>메일 제목</th>
                      <th>수신자</th>
                      <th>보낸 날짜</th>
                      <th>첨부파일</th>
                      <th>발신자</th>
                  </tr>
              </thead>
              <tbody>
        `;

        // 데이터가 있을 경우 테이블 행 추가
        if (mailList.length > 0) {
            mailList.forEach((mail, index) => {
                tableHtml += `
                    <tr>
                        <td>${index + 1}</td>
                        <td><span class="showContent" data-index="${index}" style="cursor:pointer; color:blue;">${mail[1]}</span></td>
                        <td >${mail[2].trim()}</td>
                        <td>${mail[4].replace("T","<br>")}</td>
                        <td>${mail[5].replace("static/cert_DS/","") || ''}</td>
                        <td>${mail[6]}</td>
                    </tr>
                `;
            });
        } else {
            tableHtml += `
                <tr>
                    <td colspan="6" class="text-center">보낸 메일이 없습니다.</td>
                </tr>
            `;
        }
        tableHtml += `</tbody></table></div>`;
        // 테이블 업데이트
        $("#sentMailTable").html(tableHtml);

        // 메일 제목 클릭 시 상세 보기 이벤트 추가
        $(document).on("click", ".showContent", function() {
            const index = $(this).data("index");
            showMailDetail(index, response.recordset_content);
        });        
    },
    error: function(xhr, status, error) {
        console.error("메일 리스트 불러오기 실패:", error);
        $("#sentMailTable").html(`<p class="text-danger">메일을 불러오는 중 오류가 발생했습니다.</p>`);
    }
  });
};
const showMailDetail = (index, mailContents) => {
    const mail = mailContents[index];
    console.log(mail)
    let detailHtml = `
        <h4>${mail[5]}</h4>
        <p><strong>첨부파일 개수:</strong> ${mail[2]}</p>
        <p><strong>파일 경로:</strong> ${mail[3]}</p>
        <p><strong>파일명:</strong> ${mail[4]}</p>
        ${mail[1]}
    `;
    $("#mailIframe").attr("srcdoc", detailHtml);
};

// 로딩 마스크가 이미 존재한다면, 새 계정명을 업데이트
const showLoading = (message) => {
  if ($("#loading-mask").length != 0) {
    $("#loading-mask").show();
  } else {
    // 로딩 마스크가 없으면 추가
    $('body').append(`
    <div id="loading-mask" style="position:fixed; top:0; left:0; width:100%; height:100%; background-color: rgba(0, 0, 0, 0.5); z-index: 9999; display:flex; align-items:center; justify-content:center;">
      <div style="color:white; font-size:24px; text-align:center;">
        <div class="spinner-border text-light" role="status" style="margin-bottom: 10px;">
          <span class="sr-only"></span>
        </div>
        <div>${message}...</div>
      </div>
    </div>
    `);
  }
};

const hideLoading = () => {
  $("#loading-mask").hide();
};

function loadShortcuts() {
    var shortcutMenu = document.getElementById('shortcutMenu');
    
    // ★ [추가] 요소가 없으면(null이면) 함수 중단
    if (!shortcutMenu) {
        return; 
    }

}
